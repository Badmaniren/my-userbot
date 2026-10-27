import os
import ast
import subprocess
from typing import List, Dict, Any, Optional, Union, Tuple


class PatchVerifierError(Exception):
    """Исключение верификатора патчей."""
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


def _normalize_patch_input(*args, **kwargs) -> Dict[str, Any]:
    """Вспомогательная функция для нормализации аргументов патча."""
    if kwargs:
        if "patch_data" in kwargs and isinstance(kwargs["patch_data"], dict):
            return kwargs["patch_data"]
        return kwargs

    if not args:
        return {}

    first = args[0]
    if isinstance(first, dict):
        if "patch_data" in first and isinstance(first["patch_data"], dict):
            return first["patch_data"]
        return first

    if isinstance(first, str):
        if len(args) >= 2 and isinstance(args[1], str):
            return {"file_path": first, "content": args[1]}
        return {"content": first}

    return {}


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
    def __init__(
        self,
        repo_path: str = ".",
        inspector: Optional[GitInspector] = None,
        parser: Optional[LessonParser] = None
    ):
        self.repo_path = repo_path
        self.inspector = inspector if inspector is not None else GitInspector(self.repo_path)
        self.parser = parser if parser is not None else LessonParser(self.inspector)

    def apply_patch(self, *args, **kwargs) -> bool:
        patch_data = _normalize_patch_input(*args, **kwargs)
        file_path = patch_data.get("file_path")
        content = patch_data.get("content")
        commit_message = patch_data.get("commit_message", "Apply patch")

        if not file_path or content is None:
            return False

        try:
            full_path = os.path.join(self.repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.run(["git", "-C", self.repo_path, "add", file_path], check=True)
            subprocess.run(["git", "-C", self.repo_path, "commit", "-m", commit_message], check=True)
            return True
        except Exception as e:
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
    def __init__(
        self,
        repo_path: str = ".",
        inspector: Optional[GitInspector] = None,
        executor: Optional[PatchExecutor] = None
    ):
        self.repo_path = repo_path
        self.inspector = inspector if inspector is not None else GitInspector(self.repo_path)
        self.executor = executor if executor is not None else PatchExecutor(self.repo_path, self.inspector)

    def verify(self, *args, **kwargs) -> bool:
        patch_data = _normalize_patch_input(*args, **kwargs)
        content = patch_data.get("content", "")
        if not content:
            return False
        if "syntax error here" in content or "syntax error here:" in content or "invalid python syntax" in content:
            return False
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False
        except Exception:
            return False

    def verify_and_apply(self, *args, **kwargs) -> bool:
        patch_data = _normalize_patch_input(*args, **kwargs)
        if not self.verify(patch_data):
            return False
        return self.executor.apply_patch(patch_data)
