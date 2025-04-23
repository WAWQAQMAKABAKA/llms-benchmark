import json
import os

def create_qa_benchmark(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)

    tasks = []
    for item in qa_data:
        prompt = f"Question: {item['question']}\nAnswer:"
        tasks.append({
            "prompt": prompt,
            "answer": item["answer"],
            "type": "qa"
        })

    return tasks

def create_code_benchmark(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code_data = json.load(f)

    tasks = []
    for item in code_data:
        prompt = f"{item['prompt']}\n\nWrite your code below:\n"
        tasks.append({
            "prompt": prompt,
            "answer": item["solution"],
            "type": "code"
        })

    return tasks

def create_summarization_benchmark(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        summarization_data = json.load(f)

    tasks = []
    for item in summarization_data:
        prompt = f"Summarize the following text:\n\n{item['text']}\n\nSummary:"
        tasks.append({
            "prompt": prompt,
            "answer": item["summary"],
            "type": "summarization"
        })

    return tasks

def create_reasoning_benchmark(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reasoning_data = json.load(f)

    tasks = []
    for item in reasoning_data:
        prompt = f"Reason logically and answer the question:\n\n{item['question']}\nAnswer:"
        tasks.append({
            "prompt": prompt,
            "answer": item["answer"],
            "type": "reasoning"
        })

    return tasks

def load_all_benchmarks(data_dir):
    return {
        "qa": create_qa_benchmark(os.path.join(data_dir, "qa_benchmark.json")),
        "code": create_code_benchmark(os.path.join(data_dir, "code_benchmark.json")),
        "summarization": create_summarization_benchmark(os.path.join(data_dir, "summarization_benchmark.json")),
        "reasoning": create_reasoning_benchmark(os.path.join(data_dir, "reasoning_benchmark.json"))
    }
