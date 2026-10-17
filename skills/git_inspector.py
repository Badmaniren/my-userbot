import os
import subprocess

class GitInspector:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def _run_git(self, args):
        cmd = ['git', '-C', self.repo_path] + args
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout = result.stdout
            if isinstance(stdout, bytes):
                stdout = stdout.decode('utf-8')
            if stdout is None:
                return ""
            if len(args) == 1:
                return stdout.strip('\r\n')
            return stdout
        except Exception:
            return ""

    def get_commit_history(self, max_count=50):
        cmd = ["log", f"-n {max_count}", "--pretty=format:%H|%an|%s"]
        output = self._run_git(cmd)
        if isinstance(output, bytes):
            output = output.decode('utf-8')
        output = output.strip()
        if not output:
            return []

        history = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) == 3:
                history.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'message': parts[2]
                })
        return history

    def get_file_diff(self, commit_hash):
        return self._run_git(["show", commit_hash])

    def analyze_repository(self):
        history = self.get_commit_history(max_count=1000)
        
        total_files = 0
        for root, dirs, files in os.walk(self.repo_path):
            if '.git' in root.split(os.sep):
                continue
            total_files += len(files)

        latest_commit = history[0] if history else None

        return {
            'total_commits': len(history),
            'total_files': total_files,
            'repo_path': self.repo_path,
            'latest_commit': latest_commit
        }

    def read_file_at_commit(self, commit_hash, file_path):
        return self._run_git(["show", f"{commit_hash}:{file_path}"])

    def get_history(self, max_count=1000):
        return self.get_commit_history(max_count=max_count)

    def get_latest_changes(self):
        return self._run_git(["show", "HEAD"])
