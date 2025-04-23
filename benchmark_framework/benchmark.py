import os
import time
import json
import tracemalloc
from statistics import mean
from difflib import SequenceMatcher
import ollama
from bert_score import score as bert_score
import threading
import sys
import itertools
import re
import ast

class LLMBenchmark:
    def __init__(self, models, tasks):
        self.models = models
        self.tasks = tasks
        self.results = {}
        self._thinking = False
        os.makedirs("results", exist_ok=True)

    def run_benchmarks(self):
        for model in self.models:
            self.results[model] = {}
            print(f"\n\033[1mBenchmarking model: {model}\033[0m\n" + "="*50)

            for task_type, task_data in self.tasks.items():
                print(f"\n\033[1mRunning task: {task_type} ({len(task_data)} items)\033[0m")
                task_results = self.benchmark_task(model, task_type, task_data)
                self.results[model][task_type] = task_results

                with open(f"results/{model}_{task_type}_results.json", "w", encoding="utf-8") as f:
                    json.dump(task_results, f, indent=2)

        return self.results

    def benchmark_task(self, model, task_type, task_data):
        task_results = []

        for i, item in enumerate(task_data):
            prompt = item["prompt"]
            ground_truth = item["answer"]

            start_time = time.time()
            tracemalloc.start()

            self._thinking = True
            anim_thread = threading.Thread(target=self.thinking_animation)
            anim_thread.start()

            response = ollama.chat(model=model, messages=[
                {"role": "user", "content": prompt}
            ])["message"]["content"]

            self._thinking = False
            anim_thread.join()

            latency = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            score = self.evaluate(response, ground_truth, task_type)

            self._display_interaction(prompt, response, score, latency)

            task_results.append({
                "prompt": prompt,
                "ground_truth": ground_truth,
                "response": response,
                "latency": latency,
                "memory_kb": peak / 1024,
                "score": score
            })

        return task_results

    #extension suggested in the notebook
    def thinking_animation(self):
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if not self._thinking:
                break
            sys.stdout.write(f'\r🤔 Thinking... {c}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * 20 + '\r')

    def evaluate(self, response, ground_truth, task_type):
        response = response.strip().lower()
        ground_truth = ground_truth.strip().lower()

        if task_type == "qa":
            return self.evaluate_qa(response, ground_truth)
        elif task_type == "code":
            return self.evaluate_code(response, ground_truth)
        elif task_type == "summarization":
            return self.evaluate_summarization(response, ground_truth)
        elif task_type == "reasoning":
            return self.evaluate_reasoning(response, ground_truth)
        else:
            return 0.0

    #QA V1

    #def evaluate_qa(self, response, ground_truth):
    #    return float(ground_truth in response or response in ground_truth or SequenceMatcher(None, response, ground_truth).ratio() > 0.9)

    #QA V2
    def evaluate_qa(self, response, ground_truth):
        response = response.strip().lower() #make sure they are in lowercase
        ground_truth = ground_truth.strip().lower() #make sure they are in lowercase

        if ground_truth in response or response in ground_truth:
            return 1.0
    
        # token-level Jaccard similarity
        response_tokens = set(response.split())
        ground_truth_tokens = set(ground_truth.split())
        intersection = response_tokens & ground_truth_tokens
        union = response_tokens | ground_truth_tokens

        jaccard_score = len(intersection) / len(union) if union else 0

        # Or fuzzy string similarity
        similarity_score = SequenceMatcher(None, response, ground_truth).ratio()

        # Take the max of both
        return max(jaccard_score, similarity_score) #in return two score are performed but the max score
    
    #CODE V1
    #def evaluate_code(self, response, ground_truth):
        #norm_response = ''.join(response.split())
        #norm_ground = ''.join(ground_truth.split())
        #return SequenceMatcher(None, norm_response, norm_ground).ratio()

    #CODE V2
    # you should able to let ground truth and response, 
    # and then give them same output and see if they return the same. 
    # instead of simplily matching them

    def extract_code(self, response: str) -> str:
        """
        Extracts the first code block from a response that may include markdown, text, and code.
        """
        code_blocks = re.findall(r"```(?:python)?\n(.*?)```", response, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()

        # Fallback: extract lines starting from first function
        lines = response.splitlines()
        code_lines = []
        in_code = False
        for line in lines:
            if line.strip().startswith("def "):
                in_code = True
            if in_code:
                code_lines.append(line)
        return "\n".join(code_lines).strip()

    def evaluate_code(self, response, ground_truth, func_name="func"):
        """
        Evaluates code by functional execution if possible, otherwise falls back to AST similarity.
        """
        response_code = self.extract_code(response)
        ground_truth_code = ground_truth.strip()

        # Try to execute the response code just to check for syntax/validity
        try:
            local_env = {}
            exec(response_code, {}, local_env)
            exec(ground_truth_code, {}, {})  # ground truth should be valid too
            return 0.8 + 0.2 * self.ast_similarity(response_code, ground_truth_code)
        except Exception:
            return self.ast_similarity(response_code, ground_truth_code)

    def ast_similarity(self, code1: str, code2: str) -> float:
        try:
            return SequenceMatcher(
                None,
                ast.dump(ast.parse(code1)),
                ast.dump(ast.parse(code2))
            ).ratio()
        except:
            return 0.0

    def evaluate_summarization(self, response, ground_truth):
        try:
            P, R, F1 = bert_score([response], [ground_truth], lang="en", verbose=False)
            return float(F1[0])
        except Exception as e:
            print(f"⚠️ BERTScore failed (summarization): {e}")
            return 0.0

    def evaluate_reasoning(self, response, ground_truth):
        try:
            P, R, F1 = bert_score([response], [ground_truth], lang="en", verbose=False)
            return float(F1[0])
        except Exception as e:
            print(f"⚠️ BERTScore failed (reasoning): {e}")
            return 0.0

    def get_summary_statistics(self):
        summary = {}
        for model, task_sets in self.results.items():
            summary[model] = {}
            for task_type, records in task_sets.items():
                scores = [r["score"] for r in records]
                latencies = [r["latency"] for r in records]
                memory_usages = [r["memory_kb"] for r in records]

                summary[model][task_type] = {
                    "avg_score": round(mean(scores), 4),
                    "avg_latency_sec": round(mean(latencies), 4),
                    "avg_memory_kb": round(mean(memory_usages), 2),
                }

        return summary

    def _display_interaction(self, prompt, response, score=None, latency=None):
        divider = "-" * 50
        print(f"\033[95m\nPrompt:\033[0m\n{prompt.strip()}")
        print(f"\033[94m\nModel Response:\033[0m\n{response.strip()}")

        if score is not None:
            print(f"\n\033[92mScore:\033[0m {score:.2f}")
        if latency is not None:
            print(f"\033[93mLatency:\033[0m {latency:.2f} sec")
        print(f"\033[90m{divider}\033[0m")