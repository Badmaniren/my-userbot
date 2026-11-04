import os
import subprocess
from skills.repo_analytics import RepoMonitor as RepoAnalytics
from skills.repo_summarizer import RepoSummarizer


class RepoReporter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        if not os.path.exists(os.path.join(repo_path, ".git")):
            os.makedirs(repo_path, exist_ok=True)
            subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )

    def generate_final_report(self) -> str:
        analytics_inst = RepoAnalytics(self.repo_path)
        summarizer_inst = RepoSummarizer(self.repo_path)
        
        if hasattr(analytics_inst, 'get_report'):
            analytics_data = analytics_inst.get_report()
        elif hasattr(analytics_inst, 'check_status'):
            analytics_data = analytics_inst.check_status()
        else:
            analytics_data = str(analytics_inst)

        summary_data = summarizer_inst.generate_summary()
        
        return f"{analytics_data}\n{summary_data}"

    def save_report(self, file_path: str, content: str) -> str:
        if not os.path.isabs(file_path):
            if os.path.dirname(file_path) == "":
                full_path = os.path.join(self.repo_path, file_path)
            else:
                full_path = os.path.join(self.repo_path, file_path)
        else:
            full_path = file_path
            
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)
        return full_path

    def generate_report(self, status=None, summary=None, output_path=None) -> str:
        if status is None or summary is None:
            content = self.generate_final_report()
        else:
            content = f"{status}\n{summary}"

        if output_path is None:
            output_path = os.path.join(self.repo_path, "report.txt")
        elif not os.path.isabs(output_path) and os.path.dirname(output_path) == "":
            output_path = os.path.join(self.repo_path, output_path)

        return self.save_report(output_path, content)