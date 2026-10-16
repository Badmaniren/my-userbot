import subprocess

class AnomalyDetectorError(Exception):
    pass

class AutonomousEngineError(Exception):
    pass

class CodeSanitizerError(Exception):
    pass

class CodeValidatorError(Exception):
    pass

class HypothesisGeneratorError(Exception):
    pass

class LessonParserError(Exception):
    pass

class PatchAutocorrectorError(Exception):
    pass

class PatchExecutorError(Exception):
    pass

class StabilityDigestError(Exception):
    pass

class SystemTelemetryError(Exception):
    pass


class GitInspector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _run_git_command(self, args):
        cmd = ['git', '-C', self.repo_path] + args
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return result.stdout

    def get_commit_history(self, max_count: int = 10):
        return self._run_git_command(['log', f'-n', str(max_count)])

    def get_file_diff(self, commit_hash: str):
        return self._run_git_command(['show', commit_hash])

    def analyze_repository(self):
        return self._run_git_command(['status'])

    def read_file_at_commit(self, commit_hash: str, file_path: str):
        return self._run_git_command(['show', f'{commit_hash}:{file_path}'])

    def get_history(self):
        return self.get_commit_history()

    def get_latest_changes(self):
        return self._run_git_command(['log', '-n', '1'])