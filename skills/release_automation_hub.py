from skills.release_pipeline import ReleasePipeline
from skills.repo_reporter import RepoReporter


class ReleaseAutomationHub:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        try:
            self.pipeline = ReleasePipeline(self.repo_path)
        except Exception:
            self.pipeline = None
        try:
            self.reporter = RepoReporter(self.repo_path)
        except Exception:
            self.reporter = None

    def execute_release_cycle(self, output_path: str) -> bool:
        if self.pipeline is not None:
            pipeline_success = self.pipeline.run(output_path)
        else:
            pipeline_success = False

        if self.reporter is not None:
            report_content = self.reporter.generate_final_report()
            self.reporter.save_report(output_path, report_content)
        
        return pipeline_success

    def execute_release_with_report(self, output_path: str) -> bool:
        return self.execute_release_cycle(output_path)