import subprocess
import os

class ChangelogGenerator:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or "."

    def generate(self, output_path=None):
        cmd = ["git", "-C", self.repo_path, "log", "--oneline"]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            log_output = result.stdout
        except Exception:
            log_output = ""

        changelog = f"# Changelog\n\n{log_output}"
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(changelog)
                
        return changelog

    def get_changelog(self, output_path=None):
        return self.generate(output_path)