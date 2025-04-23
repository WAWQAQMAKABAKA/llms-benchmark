import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def set_plotting_style():
    sns.set(style="whitegrid")
    plt.rcParams.update({
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16
    })

def create_visualizations(summary, results_dir='results'):
    os.makedirs(results_dir, exist_ok=True)
    set_plotting_style()

    df = pd.DataFrame.from_dict({
        (model, task): metrics
        for model, tasks in summary.items()
        for task, metrics in tasks.items()
    }, orient='index').reset_index()
    df.columns = ['model', 'task', 'avg_score', 'avg_latency_sec', 'avg_memory_kb']

    # Create and save plots
    create_bar_chart(df, 'avg_score', 'Model Accuracy by Task', results_dir)
    create_bar_chart(df, 'avg_latency_sec', 'Model Latency (sec) by Task', results_dir)
    create_bar_chart(df, 'avg_memory_kb', 'Model Memory Usage (KB) by Task', results_dir)
    create_performance_vs_latency_scatter(df, results_dir)
    create_performance_dashboard(df, results_dir)
    create_enhanced_radar_chart(df, results_dir)
    create_enhanced_heatmap(summary, results_dir)

def create_bar_chart(df, metric, title, results_dir):
    plt.figure(figsize=(10, 6))
    sns.barplot(x="task", y=metric, hue="model", data=df)
    plt.title(title)
    plt.ylabel(metric.replace("_", " ").title())
    plt.xlabel("Task")
    plt.legend(title="Model")
    for i, bar in enumerate(plt.gca().patches):
        height = bar.get_height()
        plt.gca().annotate(f"{height:.2f}", (bar.get_x() + bar.get_width() / 2, height),
                           ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{metric}_bar_chart.png"))
    plt.close()

def create_performance_vs_latency_scatter(df, results_dir):
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x="avg_latency_sec", y="avg_score", hue="model", style="task", s=100)
    plt.title("Performance vs Latency")
    plt.xlabel("Latency (sec)")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "performance_vs_latency.png"))
    plt.close()

def create_performance_dashboard(df, results_dir):
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    sns.barplot(ax=axs[0], x="task", y="avg_score", hue="model", data=df)
    axs[0].set_title("Accuracy")
    sns.barplot(ax=axs[1], x="task", y="avg_latency_sec", hue="model", data=df)
    axs[1].set_title("Latency (sec)")
    sns.barplot(ax=axs[2], x="task", y="avg_memory_kb", hue="model", data=df)
    axs[2].set_title("Memory (KB)")
    for ax in axs:
        for bar in ax.patches:
            height = bar.get_height()
            ax.annotate(f"{height:.2f}", (bar.get_x() + bar.get_width() / 2, height),
                        ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "performance_dashboard.png"))
    plt.close()

def create_enhanced_radar_chart(df, results_dir):
    import matplotlib.pyplot as plt
    from math import pi

    df_pivot = df.pivot(index="model", columns="task", values="avg_score")
    categories = list(df_pivot.columns)
    models = df_pivot.index.tolist()
    N = len(categories)

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    plt.figure(figsize=(8, 8))
    for model in models:
        values = df_pivot.loc[model].tolist()
        values += values[:1]
        plt.polar(angles, values, label=model, marker='o')

    plt.xticks(angles[:-1], categories, color='gray')
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], color="gray", size=8)
    plt.title("Model Comparison by Task (Accuracy)", size=14)
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "radar_chart.png"))
    plt.close()

def create_enhanced_heatmap(summary, results_dir):
    # Score Heatmap
    scores = {
        model: {task: metrics["avg_score"] for task, metrics in tasks.items()}
        for model, tasks in summary.items()
    }
    df_score = pd.DataFrame(scores).T
    plt.figure(figsize=(8, 6))
    sns.heatmap(df_score, annot=True, cmap="YlGnBu", fmt=".2f")
    plt.title("Heatmap of Accuracy by Model & Task")
    plt.savefig(os.path.join(results_dir, "score_heatmap.png"))
    plt.close()

    # Latency Heatmap
    latency = {
        model: {task: metrics["avg_latency_sec"] for task, metrics in tasks.items()}
        for model, tasks in summary.items()
    }
    df_latency = pd.DataFrame(latency).T
    plt.figure(figsize=(8, 6))
    sns.heatmap(df_latency, annot=True, cmap="YlOrRd", fmt=".2f")
    plt.title("Heatmap of Latency by Model & Task")
    plt.savefig(os.path.join(results_dir, "latency_heatmap.png"))
    plt.close()
