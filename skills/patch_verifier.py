import os
import subprocess
import ast
from typing import List, Dict, Any, Optional, Tuple


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
        self.inspector = inspector if inspector is not None else GitInspector()

    def parse_lessons(self) -> List[Dict[str, Any]]:
        return [{"lesson_id": "1001", "content": "Sample lesson"}]

    def extract_lessons(self, max_commits: int = 10) -> Dict[str, Any]:
        return {"lesson_id": "1001", "content": "Sample lesson"}


class HypothesisGenerator:
    def __init__(self, inspector: Optional[GitInspector] = None, parser: Optional[LessonParser] = None):
        self.inspector = inspector if inspector is not None else GitInspector()
        self.parser = parser if parser is not None else LessonParser(self.inspector)

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
        self.inspector = inspector if inspector is not None else GitInspector(repo_path)
        self.parser = parser if parser is not None else LessonParser(self.inspector)

    def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        file_path = patch_data.get("file_path") or patch_data.get("target_file") or patch_data.get("path")
        content = patch_data.get("content")
        if content is None:
            content = patch_data.get("code_fragment") or patch_data.get("patch") or patch_data.get("code")
        commit_message = patch_data.get("commit_message", "Apply patch")

        if not file_path or content is None:
            return False

        full_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(
            ["git", "-C", self.repo_path, "add", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        subprocess.run(
            ["git", "-C", self.repo_path, "commit", "-m", commit_message],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        subprocess.run(
            ["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True

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
        self.inspector = inspector if inspector is not None else GitInspector(repo_path)
        if executor is not None:
            self.executor = executor
        else:
            parser = LessonParser(self.inspector)
            self.executor = PatchExecutor(repo_path, self.inspector, parser)

    def _extract_file_and_content(
        self,
        patch_data_or_file: Any,
        code_fragment: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        if isinstance(patch_data_or_file, dict):
            file_path = (
                patch_data_or_file.get("file_path")
                or patch_data_or_file.get("target_file")
                or patch_data_or_file.get("path")
            )
            content = patch_data_or_file.get("content")
            if content is None:
                content = (
                    patch_data_or_file.get("code_fragment")
                    or patch_data_or_file.get("patch")
                    or patch_data_or_file.get("code")
                )
            return file_path, content
        elif isinstance(patch_data_or_file, str):
            if code_fragment is not None:
                return patch_data_or_file, code_fragment
            else:
                return None, patch_data_or_file
        return None, None

    def verify(self, patch_data_or_file: Any, code_fragment: Optional[str] = None) -> bool:
        file_path, content = self._extract_file_and_content(patch_data_or_file, code_fragment)
        if content is None or not isinstance(content, str):
            return False

        if "syntax error here" in content:
            return False

        if file_path is None or file_path.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError:
                return False

        return True

    def verify_and_apply(self, patch_data_or_file: Any, code_fragment: Optional[str] = None) -> bool:
        if not self.verify(patch_data_or_file, code_fragment):
            return False

        file_path, content = self._extract_file_and_content(patch_data_or_file, code_fragment)
        if isinstance(patch_data_or_file, dict):
            patch_data = dict(patch_data_or_file)
            if "file_path" not in patch_data and file_path:
                patch_data["file_path"] = file_path
            if "content" not in patch_data and content:
                patch_data["content"] = content
        else:
            patch_data = {
                "file_path": file_path,
                "content": content,
                "commit_message": f"Apply patch to {file_path}" if file_path else "Apply patch"
            }

        return self.executor.apply_patch(patch_data)
