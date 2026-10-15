import os
import subprocess

class GitInspector:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def get_commit_history(self, max_count=50):
        cmd = [
            'git', '-C', self.repo_path, 'log',
            f'-n', str(max_count),
            '--pretty=format:%h|%an|%s'
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            output = result.stdout.decode('utf-8').strip()
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
        except subprocess.CalledProcessError:
            return []

    def get_file_diff(self, commit_hash):
        cmd = [
            'git', '-C', self.repo_path, 'show',
            commit_hash
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError:
            return ""

    def analyze_repository(self):
        history = self.get_commit_history(max_count=1000)
        
        total_files = 0
        for root, dirs, files in os.walk(self.repo_path):
            if '.git' in root.split(os.sep):
                continue
            total_files += len(files)

        return {
            'total_commits': len(history),
            'total_files': total_files,
            'repo_path': self.repo_path
        }

    def get_changed_files_at_commit(self, commit_hash):
        cmd = [
            'git', '-C', self.repo_path, 'show',
            '--name-only', '--format=', commit_hash
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            output = result.stdout.decode('utf-8').strip()
            if not output:
                return []
            return [line.strip() for line in output.split('\n') if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def read_file_at_commit(self, commit_hash, file_path):
        cmd = [
            'git', '-C', self.repo_path, 'show',
            f"{commit_hash}:{file_path}"
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError:
            return ""

    def get_history(self):
        return self.get_commit_history(max_count=1000)

    def get_latest_changes(self):
        cmd = [
            'git', '-C', self.repo_path, 'show', 'HEAD'
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError:
            return ""