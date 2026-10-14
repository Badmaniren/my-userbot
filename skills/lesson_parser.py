import io
import re
from skills.git_inspector import GitInspector


class LessonParser:
    def __init__(self, repo_path_or_inspector):
        if hasattr(repo_path_or_inspector, 'get_commit_history') and hasattr(repo_path_or_inspector, 'read_file_at_commit'):
            self.inspector = repo_path_or_inspector
            if hasattr(self.inspector, 'repo_path'):
                self.repo_path = self.inspector.repo_path
            else:
                self.repo_path = None
        else:
            self.repo_path = repo_path_or_inspector
            self.inspector = GitInspector(self.repo_path)

    def extract_failure_history(self, max_commits=10):
        commits = self.inspector.get_commit_history(max_count=max_commits)
        failure_history = []
        for commit in commits:
            commit_hash = commit['hash']
            message = commit['message']
            diff = self.inspector.get_file_diff(commit_hash)
            failure_history.append({
                'commit_hash': commit_hash,
                'message': message,
                'diff': diff
            })
        return failure_history

    def parse_anticheat_errors(self, commit_hash, file_path):
        file_stream = self.inspector.read_file_at_commit(commit_hash, file_path)
        if isinstance(file_stream, io.BytesIO):
            content = file_stream.read().decode('utf-8')
        elif isinstance(file_stream, (bytes, bytearray)):
            content = file_stream.decode('utf-8')
        else:
            content = str(file_stream)

        matches = re.findall(r'ANTICHEAT_VIOLATION_\w+', content)
        if matches:
            return matches

        errors = []
        for line in content.splitlines():
            if 'ANTICHEAT_VIOLATION_' in line:
                for quote in ["'", '"']:
                    if quote in line:
                        parts = line.split(quote)
                        for p in parts:
                            if 'ANTICHEAT_VIOLATION_' in p:
                                errors.append(p.strip())
                                break
                        else:
                            errors.append(line.strip())
                        break
                else:
                    errors.append(line.strip())
        return errors

    def get_fix_commits(self):
        commits = self.inspector.get_commit_history()
        fix_commits = []
        for commit in commits:
            message = commit['message']
            if message.startswith('fix'):
                fix_commits.append({
                    'hash': commit['hash'],
                    'message': message
                })
        return fix_commits

    def parse_lesson_history(self, file_path):
        commits = self.inspector.get_commit_history()
        if not commits:
            raise Exception("No commits found in repository")

        latest_commit = commits[0]['hash']
        file_stream = self.inspector.read_file_at_commit(latest_commit, file_path)
        if isinstance(file_stream, io.BytesIO):
            content = file_stream.read().decode('utf-8')
        elif isinstance(file_stream, (bytes, bytearray)):
            content = file_stream.decode('utf-8')
        else:
            content = str(file_stream)

        failures = []
        fixes = []
        anticheat_errors = []

        for line in content.splitlines():
            if "Failure history:" in line:
                failures.append(line.split("Failure history:")[1].strip())
            if "Fix applied:" in line:
                fixes.append(line.split("Fix applied:")[1].strip())
            if "Anticheat error:" in line:
                anticheat_errors.append(line.split("Anticheat error:")[1].strip())

        return {
            "failures": failures,
            "fixes": fixes,
            "anticheat_errors": anticheat_errors
        }

    def parse(self, file_path=None):
        if not file_path:
            raise ValueError("file_path is required")
        return self.parse_lesson_history(file_path)

    def get_context_for_file(self, file_path, max_commits=10):
        if not file_path:
            raise ValueError("file_path is required")
        history = self.extract_failure_history(max_commits=max_commits)
        fixes = self.get_fix_commits()
        lesson_history = self.parse_lesson_history(file_path)
        return {
            "history": history,
            "fixes": fixes,
            "lesson_history": lesson_history
        }

    def analyze_file_history(self, file_path):
        if not file_path:
            raise ValueError("file_path is required")
        return self.get_context_for_file(file_path)

    def parse_latest_change(self, file_path):
        if not file_path:
            raise ValueError("file_path is required")
        commits = self.inspector.get_commit_history(max_count=1)
        if not commits:
            raise Exception("No commits found in repository")
        latest_hash = commits[0]['hash']
        diff = self.inspector.get_file_diff(latest_hash)
        return {
            "commit_hash": latest_hash,
            "message": commits[0]['message'],
            "diff": diff
        }

    def extract_error_patterns(self, commit_hash=None, file_path=None):
        if not commit_hash or not file_path:
            commits = self.inspector.get_commit_history(max_count=1)
            if not commits:
                raise Exception("No commits found in repository")
            commit_hash = commit_hash or commits[0]['hash']
            if not file_path:
                raise ValueError("file_path is required")
        return self.parse_anticheat_errors(commit_hash, file_path)

    def prepare_hypothesis_data(self, file_path=None):
        if not file_path:
            raise ValueError("file_path is required")
        lesson_data = self.parse_lesson_history(file_path)
        return {
            "failures": lesson_data.get("failures", []),
            "fixes": lesson_data.get("fixes", []),
            "anticheat_errors": lesson_data.get("anticheat_errors", [])
        }
