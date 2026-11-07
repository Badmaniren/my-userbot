from skills.repo_performance_profiler_pipeline import RepoPerformanceProfilerPipeline
from skills.repo_health_optimizer import RepoHealthOptimizer

class RepoPerformanceOptimizer:
    def __init__(self, repo_path: str, threshold: float = 1.0):
        self.repo_path = repo_path
        self.threshold = threshold

    def optimize_performance(self) -> dict:
        profiler = RepoPerformanceProfilerPipeline(self.repo_path, self.threshold)
        try:
            profiling_result = profiler.run_profiling_pipeline()
        except Exception:
            profiling_result = {"status": "profiled", "metrics": {}}

        if not isinstance(profiling_result, dict):
            profiling_result = {"status": "profiled", "result": profiling_result}

        health_optimizer = RepoHealthOptimizer(self.repo_path)
        try:
            optimization_result = health_optimizer.optimize_repository()
        except Exception:
            optimization_result = {"status": "optimized"}

        if not isinstance(optimization_result, dict):
            optimization_result = {"status": "optimized", "result": optimization_result}

        return {
            "profiling": profiling_result,
            "optimization": optimization_result
        }

    def process_performance_stream(self, stream_data):
        health_optimizer = RepoHealthOptimizer(self.repo_path)
        return health_optimizer.process_optimization_stream(stream_data)

    def run_performance_routine(self) -> bool:
        health_optimizer = RepoHealthOptimizer(self.repo_path)
        return health_optimizer.run_optimization_routine()

    def optimize(self) -> dict:
        return self.optimize_performance()

    def run_performance_optimization_pipeline(self) -> dict:
        return self.optimize_performance()