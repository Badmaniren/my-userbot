from skills.repo_monitor import RepoMonitor
from skills.repo_health_diagnostic import RepoHealthDiagnostic

class RepoPerformanceProfilerPipeline:
    def __init__(self, repo_path: str, threshold: float):
        self.repo_path = repo_path
        self.threshold = threshold

    def run_profiling_pipeline(self) -> dict:
        monitor = RepoMonitor(self.repo_path)
        repo_status = monitor.check_status()

        diagnostic = RepoHealthDiagnostic()
        diagnostic_results = diagnostic.perform_deep_health_check(self.repo_path, self.threshold)

        # Выбираем ключ метрики для оценки порогового значения:
        # используем первый попавшийся ключ (кроме "status"), либо "health_score", либо дефолтный.
        metric_key = None
        for key in diagnostic_results.keys():
            if key != "status":
                metric_key = key
                break
        if not metric_key:
            metric_key = "health_score"

        threshold_passed = diagnostic.evaluate_threshold(diagnostic_results, metric_key, self.threshold)
        report_stream = diagnostic.export_report_stream(self.repo_path)
        report_stream_content = report_stream.read() if report_stream else ""

        return {
            "repo_status": repo_status,
            "diagnostic_results": diagnostic_results,
            "threshold_passed": threshold_passed,
            "report_stream_content": report_stream_content
        }


def repo_performance_profiler_pipeline(repo_path: str, profiling_id: str, threshold: float) -> dict:
    monitor = RepoMonitor(repo_path)
    monitor_status = monitor.check_status()

    diagnostic = RepoHealthDiagnostic()
    diagnostic_data = diagnostic.run_full_diagnostic(repo_path)
    is_performant = diagnostic.evaluate_threshold(diagnostic_data, "health_score", threshold)

    return {
        "profiling_id": profiling_id,
        "monitor_status": monitor_status,
        "diagnostic_data": diagnostic_data,
        "is_performant": is_performant
    }