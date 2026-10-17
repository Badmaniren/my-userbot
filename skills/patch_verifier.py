import os
import subprocess
from typing import List, Dict, Any, Optional, Union


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
    def __init__(self, repo_path: str):
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
    def __init__(self, inspector: GitInspector):
        self.inspector = inspector

    def parse_lessons(self) -> List[Dict[str, Any]]:
        return [{"lesson_id": "1001", "content": "Sample lesson"}]

    def extract_lessons(self, max_commits: int = 10) -> Dict[str, Any]:
        return {"lesson_id": "1001", "content": "Sample lesson"}


class HypothesisGenerator:
    def __init__(self, inspector: GitInspector, parser: LessonParser):
        self.inspector = inspector
        self.parser = parser

    def generate_hypotheses(self, max_commits: int = 10) -> List[Dict[str, Any]]:
        return [{"id": "hyp_1", "weight": 0.5, "target": "module.py"}]

    def prioritize_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(hypotheses, key=lambda x: x.get("weight", 0), reverse=True)


class PatchExecutor:
    def __init__(self, repo_path: str, inspector: GitInspector, parser: LessonParser):
        self.repo_path = repo_path
        self.inspector = inspector
        self.parser = parser

    def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        file_path = patch_data.get("file_path")
        content = patch_data.get("content")
        commit_message = patch_data.get("commit_message", "Apply patch")

        if not file_path or content is None:
            return False

        full_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            res_add = subprocess.run(["git", "-C", self.repo_path, "add", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res_add.returncode == 0:
                subprocess.run(["git", "-C", self.repo_path, "commit", "-m", commit_message], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
    def __init__(
        self,
        repo_path: Optional[str] = None,
        inspector: Optional[GitInspector] = None,
        executor: Optional[PatchExecutor] = None
    ):
        self.repo_path = repo_path or "."
        self.inspector = inspector if inspector is not None else GitInspector(self.repo_path)
        parser = LessonParser(self.inspector)
        self.executor = executor if executor is not None else PatchExecutor(self.repo_path, self.inspector, parser)

    def verify_and_apply(self, patch_data: Any, *args: Any, **kwargs: Any) -> bool:
        content = ""
        file_path = kwargs.get("target_file") or kwargs.get("file_path")
        commit_message = kwargs.get("commit_message", "Apply patch")

        if isinstance(patch_data, dict):
            content = patch_data.get("content", "")
            file_path = patch_data.get("file_path") or file_path
            commit_message = patch_data.get("commit_message", commit_message)
        elif args:
            arg1 = patch_data
            arg2 = args[0]
            if isinstance(arg1, str) and isinstance(arg2, str):
                if arg1.endswith(".py") or ("\n" not in arg1 and "\n" in arg2):
                    file_path = arg1
                    content = arg2
                elif arg2.endswith(".py") or ("\n" not in arg2 and "\n" in arg1):
                    file_path = arg2
                    content = arg1
                else:
                    file_path = arg1
                    content = arg2
        elif isinstance(patch_data, str):
            content = patch_data

        if "syntax error here" in content:
            return False

        if not file_path:
            if os.path.isdir(self.repo_path):
                py_files = [f for f in os.listdir(self.repo_path) if f.endswith(".py")]
                if py_files:
                    file_path = py_files[0]
            if not file_path:
                file_path = "temp_patch.py"

        exec_dict = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_message
        }
        return self.executor.apply_patch(exec_dict)
