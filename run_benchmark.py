from benchmark_framework.tasks import load_all_benchmarks
from benchmark_framework.benchmark import LLMBenchmark
from benchmark_framework.visualization import create_visualizations
from benchmark_framework.report import generate_report


def main():
    # Define models to benchmark
    models = ["llama3:8b"] #"mistral"

    # Load all benchmark tasks
    print(" Loading benchmark tasks...")
    tasks = load_all_benchmarks("data")

    # Initialize and run the benchmark
    benchmark = LLMBenchmark(models, tasks)
    print(" Running benchmarks...")
    results = benchmark.run_benchmarks()

    # Calculate summary statistics
    print(" Summarizing results...")
    summary = benchmark.get_summary_statistics()

    # Generate visualizations
    print(" Generating visualizations...")
    create_visualizations(summary, results_dir="results")

    # Generate report
    print(" Generating markdown report...")
    generate_report(summary, results, output_dir="results")

    print(" Benchmark complete. See results in the 'results/' directory.")


if __name__ == "__main__":
    main()

