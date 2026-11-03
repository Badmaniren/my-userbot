import os
from skills.repo_analytics import RepoAnalytics
from skills.repo_summarizer import RepoSummarizer


class RepoReporter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def generate_final_report(self) -> str:
        analytics_inst = RepoAnalytics(self.repo_path)
        summarizer_inst = RepoSummarizer(self.repo_path)
        
        analytics_data = analytics_inst.get_report()
        summary_data = summarizer_inst.generate_summary()
        
        return f"{analytics_data}\n{summary_data}"

    def save_report(self, file_path: str, content: str) -> str:
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def generate_report(self, status=None, summary=None, output_path=None) -> str:
        if status is None or summary is None:
            content = self.generate_final_report()
        else:
            content = f"{status}\n{summary}"

        if output_path is None:
            output_path = os.path.join(self.repo_path, "report.txt")

        return self.save_report(output_path, content)