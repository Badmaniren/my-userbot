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

        # Determine metric key:
        # If diagnostic_results is a dict, evaluate against its first key, or fallback to 'health_score' if key is 'status'
        metric_key = "health_score"
        if isinstance(diagnostic_results, dict) and diagnostic_results:
            keys = list(diagnostic_results.keys())
            if keys[0] != "status":
                metric_key = keys[0]

        try:
            threshold_passed = diagnostic.evaluate_threshold(diagnostic_results, metric_key, self.threshold)
        except (AttributeError, TypeError):
            threshold_passed = bool(diagnostic_results)

        if not isinstance(threshold_passed, bool):
            threshold_passed = bool(threshold_passed)

        report_stream = diagnostic.export_report_stream(self.repo_path)
        if hasattr(report_stream, "read"):
            report_stream_content = report_stream.read()
        else:
            report_stream_content = report_stream

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
    if not isinstance(is_performant, bool):
        is_performant = bool(is_performant)

    return {
        "profiling_id": profiling_id,
        "monitor_status": monitor_status,
        "diagnostic_data": diagnostic_data,
        "is_performant": is_performant
    }
