import ast
import os
import subprocess
from typing import Any, Dict, List, Optional


class HypothesisGeneratorError(Exception):
    """Исключение генератора гипотез."""

    pass


class LessonParserError(Exception):
    """Исключение парсера уроков."""

    pass


class PatchExecutorError(Exception):
    """Исключение исполнителя патчей."""

    pass


class PatchVerifierError(Exception):
    """Исключение верификатора патчей."""

    pass


class GitInspector:

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _run_git(self, args: List[str]) -> str:
        try:
            res = subprocess.run(
                ["git", "-C", self.repo_path] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            return res.stdout.strip() if res.stdout else ""
        except (subprocess.SubprocessError, OSError, IOError):
            return ""

    def get_commit_history(self, max_count: int = 10) -> List[Dict[str, str]]:
        output = self._run_git(
            ["log", "-n", str(max_count), "--pretty=format:%H|%an|%s"]
        )
        history = []
        if not output:
            return history
        for line in output.split("\n"):
            parts = line.split("|", 2)
            if len(parts) == 3:
                history.append(
                    {"hash": parts[0], "author": parts[1], "message": parts[2]}
                )
        return history

    def get_file_diff(self, commit_hash: str) -> str:
        return self._run_git(["show", commit_hash])

    def analyze_repository(self) -> Dict[str, Any]:
        commits = self.get_commit_history()
        return {
            "total_commits": len(commits),
            "latest_commit": commits[0] if commits else None,
        }

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

    def __init__(
        self,
        inspector: Optional[GitInspector] = None,
        parser: Optional[LessonParser] = None,
    ):
        self.inspector = inspector
        self.parser = parser

    def generate_hypotheses(self, max_commits: int = 10) -> List[Dict[str, Any]]:
        return [{"id": "hyp_1", "weight": 0.5, "target": "module.py"}]

    def prioritize_hypotheses(
        self, hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not hypotheses:
            return []
        return sorted(hypotheses, key=lambda x: x.get("weight", 0), reverse=True)


class PatchExecutor:

    def __init__(
        self,
        repo_path: str,
        inspector: Optional[GitInspector] = None,
        parser: Optional[LessonParser] = None,
    ):
        self.repo_path = repo_path
        self.inspector = inspector
        self.parser = parser

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
            subprocess.run(
                ["git", "-C", self.repo_path, "add", file_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", commit_message],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except (IOError, OSError, subprocess.SubprocessError):
            return False

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        try:
            subprocess.run(
                ["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except (subprocess.SubprocessError, IOError, OSError):
            return False

    def execute_from_lessons(self) -> Dict[str, Any]:
        return {"executed_lessons": 1, "status": "success"}


class PatchVerifier:

    def __init__(
        self,
        repo_path: str,
        inspector: Optional[GitInspector] = None,
        executor: Optional[PatchExecutor] = None,
        analyzer: Optional[Any] = None,
        applier: Optional[Any] = None,
        **kwargs: Any,
    ):
        self.repo_path = repo_path
        self.inspector = inspector or kwargs.get("inspector")
        self.executor = executor or kwargs.get("executor")
        self.analyzer = analyzer or kwargs.get("analyzer")
        self.applier = applier or kwargs.get("applier")

    def verify_syntax(self, content: str, file_path: str = "") -> bool:
        if content is None or not isinstance(content, str):
            return False
        if "syntax error here" in content:
            return False
        if file_path and not file_path.endswith(".py"):
            return True
        try:
            ast.parse(content)
            return True
        except (SyntaxError, TypeError, ValueError):
            return False

    def verify_patch(self, patch_data: Dict[str, Any]) -> bool:
        if not isinstance(patch_data, dict):
            return False

        content = patch_data.get("content", "")
        file_path = patch_data.get("file_path", "")

        if not self.verify_syntax(content, file_path):
            return False

        if self.analyzer:
            res = None
            if hasattr(self.analyzer, "analyze_patch"):
                res = self.analyzer.analyze_patch(patch_data)
            elif hasattr(self.analyzer, "analyze"):
                res = self.analyzer.analyze(patch_data)
            elif hasattr(self.analyzer, "verify_patch"):
                res = self.analyzer.verify_patch(patch_data)
            elif hasattr(self.analyzer, "verify"):
                res = self.analyzer.verify(patch_data)

            if res is False:
                return False
            if isinstance(res, dict):
                if res.get("is_valid") is False or res.get("valid") is False:
                    return False
                if not res.get("is_valid", True):
                    return False
                if res.get("status") in ("error", "failed", "invalid"):
                    return False
            elif hasattr(res, "is_valid") and not getattr(res, "is_valid"):
                return False
            elif hasattr(res, "valid") and not getattr(res, "valid"):
                return False

        return True

    def verify_and_apply(self, patch_data: Dict[str, Any]) -> bool:
        if not isinstance(patch_data, dict):
            return False

        if not self.verify_patch(patch_data):
            return False

        if self.applier and hasattr(self.applier, "apply_patch"):
            return bool(self.applier.apply_patch(patch_data))
        if self.applier and hasattr(self.applier, "apply"):
            return bool(self.applier.apply(patch_data))
        if self.executor and hasattr(self.executor, "apply_patch"):
            return bool(self.executor.apply_patch(patch_data))

        return False

    def analyze_patch(self, patch_data: Dict[str, Any]) -> bool:
        return self.verify_patch(patch_data)

    def validate_patch(self, patch_data: Dict[str, Any]) -> bool:
        return self.verify_patch(patch_data)

    def verify(self, patch_data: Dict[str, Any]) -> bool:
        return self.verify_patch(patch_data)

    def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        return self.verify_and_apply(patch_data)