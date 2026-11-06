from skills.release_pipeline import ReleasePipeline
from skills.repo_reporter import RepoReporter


class ReleaseAutomationHub:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.pipeline = ReleasePipeline(self.repo_path)
        self.reporter = RepoReporter(self.repo_path)

    def execute_release_cycle(self, output_path: str) -> bool:
        pipeline_success = self.pipeline.run(output_path)
        report_content = self.reporter.generate_final_report()
        self.reporter.save_report(output_path, report_content)
        return pipeline_success

    def execute_release_with_report(self, output_path: str) -> bool:
        return self.execute_release_cycle(output_path)