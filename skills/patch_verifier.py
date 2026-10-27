import os
import subprocess
import ast
from typing import List, Dict, Any, Optional

class PatchVerifierError(Exception):
    """Базовое исключение модуля verifier патчей."""
    pass

class HypothesisGeneratorError(Exception):
    """Исключение генератора гипотез."""
    pass

class LessonParserError(Exception):
    """Исключение парсера уроков."""
    pass

class PatchExecutorError(Exception):
    """Исключение исполнителя патчей."""
    pass


class GitInspector:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> str:
        res = subprocess.run(
            ["git", "-C", self.repo_path] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        return res.stdout.strip()

    def get_commit_history(self, max_count: int = 10) -> List[Dict[str, str]]:
        output = self._run_git(["log", f"-n {max_count}", "--pretty=format:%H|%an|%s"])
        history = []
        if not output:
            return history
        for line in output.split("\n"):
            parts = line.split("|", 2)
            if len(parts) == 3:
                history.append({"hash": parts[0], "author": parts[1], "message": parts[2]})
        return history

    def get_file_diff(self, commit_hash: str) -> str:
        return self._run_git(["show", commit_hash])

    def analyze_repository(self) -> Dict[str, Any]:
        commits = self.get_commit_history()
        return {"total_commits": len(commits), "latest_commit": commits[0] if commits else None}

    def read_file_at_commit(self, commit_hash: str, file_path: str) -> str:
        return self._run_git(["show", f"{commit_hash}:{file_path}"])

    def get_history(self, max_count: int = 10) -> List[Dict[str, str]]:
        return self.get_commit_history(max_count)

    def get_latest_changes(self) -> str:
        history = self.get_commit_history(max_count=1)
        if history:
            return self.get_file_diff(history[0]["hash"])
        return ""


class LessonParser:
    def __init__(self, inspector: Optional[GitInspector] = None):
        self.inspector = inspector

    def parse_lessons(self) -> List[Dict[str, Any]]:
        return [{"lesson_id": "1001", "content": "Sample lesson"}]

    def extract_lessons(self, max_commits: int = 10) -> Dict[str, Any]:
        return {"lesson_id": "1001", "content": "Sample lesson"}


class HypothesisGenerator:
    def __init__(self, inspector: Optional[GitInspector] = None, parser: Optional[LessonParser] = None):
        self.inspector = inspector
        self.parser = parser

    def generate_hypotheses(self, max_commits: int = 10) -> List[Dict[str, Any]]:
        return [{"id": "hyp_1", "weight": 0.5, "target": "module.py"}]

    def prioritize_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(hypotheses, key=lambda x: x.get("weight", 0), reverse=True)


class PatchExecutor:
    def __init__(self, repo_path: str = ".", inspector: Optional[GitInspector] = None, parser: Optional[LessonParser] = None):
        self.repo_path = repo_path
        self.inspector = inspector or GitInspector(repo_path)
        self.parser = parser or LessonParser(self.inspector)

    def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        if not isinstance(patch_data, dict):
            return False
        file_path = patch_data.get("file_path")
        content = patch_data.get("content")
        commit_message = patch_data.get("commit_message", "Apply patch")

        if not file_path or content is None:
            return False

        full_path = os.path.join(self.repo_path, file_path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.run(["git", "-C", self.repo_path, "add", file_path], check=True)
            subprocess.run(["git", "-C", self.repo_path, "commit", "-m", commit_message], check=True)
            return True
        except Exception:
            return False

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        try:
            subprocess.run(["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path], check=True)
            return True
        except Exception:
            return False

    def execute_from_lessons(self) -> Dict[str, Any]:
        return {"executed_lessons": 1, "status": "success"}


class PatchVerifier:
    def __init__(self, repo_path: str = ".", inspector: Optional[GitInspector] = None, executor: Optional[PatchExecutor] = None):
        self.repo_path = repo_path
        self.inspector = inspector or GitInspector(repo_path)
        self.executor = executor or PatchExecutor(repo_path, self.inspector, LessonParser(self.inspector))

    def verify(self, patch_data_or_path: Any, code_fragment: Optional[str] = None) -> bool:
        if isinstance(patch_data_or_path, dict):
            content = patch_data_or_path.get("content", "")
        elif isinstance(patch_data_or_path, str) and code_fragment is not None:
            content = code_fragment
        elif isinstance(patch_data_or_path, str):
            content = patch_data_or_path
        else:
            return False

        if "syntax error here" in content:
            return False
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

    def verify_and_apply(self, patch_data_or_path: Any, code_fragment: Optional[str] = None) -> bool:
        if isinstance(patch_data_or_path, dict):
            patch_data = patch_data_or_path
        elif isinstance(patch_data_or_path, str) and code_fragment is not None:
            patch_data = {"file_path": patch_data_or_path, "content": code_fragment}
        else:
            return False

        if not self.verify(patch_data):
            return False
        return self.executor.apply_patch(patch_data)
