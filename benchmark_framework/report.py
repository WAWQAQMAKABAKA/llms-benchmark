import os
import pandas as pd
import statistics

def generate_report(summary, all_results, output_dir='results'):
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "llm_benchmark_report.md")

    df = pd.DataFrame.from_dict({
        (model, task): metrics
        for model, tasks in summary.items()
        for task, metrics in tasks.items()
    }, orient='index').reset_index()
    df.columns = ['model', 'task', 'avg_score', 'avg_latency_sec', 'avg_memory_kb']

    # Efficiency: score per second and score per KB
    df['efficiency_score_per_sec'] = df['avg_score'] / df['avg_latency_sec']
    df['efficiency_score_per_kb'] = df['avg_score'] / df['avg_memory_kb']

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# LLM Benchmark Report\n\n")
        f.write("This report provides both quantitative metrics and qualitative insights from the benchmark tasks.\n\n")

        f.write("## Executive Summary\n")
        top_models = df.groupby('model')['avg_score'].mean().sort_values(ascending=False)
        best_model = top_models.idxmax()
        best_score = top_models.max()
        f.write(f"- **Best Performing Model**: `{best_model}` with an average score of **{best_score:.2f}**\n")
        f.write(f"- **Tasks Covered**: {df['task'].nunique()} — {', '.join(df['task'].unique())}\n")
        f.write(f"- **Efficiency (Score/sec)**: Top model is `{df.loc[df['efficiency_score_per_sec'].idxmax()]['model']}`\n")
        f.write(f"- **Efficiency (Score/KB)**: Top model is `{df.loc[df['efficiency_score_per_kb'].idxmax()]['model']}`\n\n")

        f.write("## Model Rankings\n")
        for model, score in top_models.items():
            f.write(f"- `{model}`: **{score:.2f}** average score\n")

        f.write("\n## Task Performance\n")
        for task in df['task'].unique():
            f.write(f"### Task: `{task}`\n")
            task_df = df[df['task'] == task].sort_values(by='avg_score', ascending=False)
            for _, row in task_df.iterrows():
                f.write(f"- `{row['model']}` → Score: **{row['avg_score']:.2f}**, Latency: {row['avg_latency_sec']:.2f}s, Memory: {row['avg_memory_kb']:.0f}KB\n")
            f.write("\n")

        f.write("## Efficiency Metrics\n")
        for _, row in df.iterrows():
            f.write(f"- `{row['model']} | {row['task']}` → Score/sec: **{row['efficiency_score_per_sec']:.2f}**, Score/KB: **{row['efficiency_score_per_kb']:.4f}**\n")

        f.write("\n## Example Prompts and Responses\n")
        for model, task_results in all_results.items():
            for task_type, records in task_results.items():
                if not records:
                    continue
                scores = [r['score'] for r in records]
                median_idx = scores.index(sorted(scores)[len(scores) // 2])
                best_idx = scores.index(max(scores))
                worst_idx = scores.index(min(scores))

                f.write(f"### `{model}` on `{task_type}`\n")
                for label, idx in [("Best", best_idx), ("Median", median_idx), ("Worst", worst_idx)]:
                    r = records[idx]
                    f.write(f"**{label} Example**\n")
                    f.write("```text\n")
                    f.write(f"Prompt:\n{r['prompt'].strip()}\n\n")
                    f.write(f"Response:\n{r['response'].strip()}\n\n")
                    f.write(f"Expected:\n{r['ground_truth'].strip()}\n")
                    f.write("```\n")
                    f.write(f"Score: **{r['score']:.2f}**, Latency: {r['latency']:.2f}s\n\n")

    print(f"✅ Markdown report saved to {report_path}")