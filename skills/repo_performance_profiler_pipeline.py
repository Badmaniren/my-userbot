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
        diagnostic_results = diagnostic.perform_deep_