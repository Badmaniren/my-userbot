import os
import io
from typing import List, Dict, Any, Optional

from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser, LessonParserError
from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError
from skills.patch_executor import PatchExecutor, PatchExecutorError


class PatchVerifierError(Exception):
    """Exception raised by PatchVerifier."""
    pass


class PatchVerifier:
    """Module for verifying and applying patches after syntax and sanitizer checks."""

    def __init__(
        self,
        repo_path: Optional[str] = None,
        inspector: Optional[Any] = None,
        executor: Optional[Any] = None
    ):
        self.repo_path = repo_path if repo_path is not None else "."
        self.inspector = inspector if inspector is not None else GitInspector(self.repo_path)
        if executor is not None:
            self.executor = executor
        else:
            parser = LessonParser(self.inspector)
            self.executor = PatchExecutor(self.repo_path, self.inspector, parser)

        self.sanitizer = PatchSanitizer()

    def verify_and_apply(self, patch_data: Any, content: Optional[str] = None) -> bool:
        """Verifies, sanitizes, and applies a patch."""
        if isinstance(patch_data, dict):
            p_data = dict(patch_data)
        elif isinstance(patch_data, (tuple, list)) and len(patch_data) >= 2:
            p_data = {
                "file_path": patch_data[0],
                "content": patch_data[1]
            }
        elif isinstance(patch_data, str):
            p_data = {
                "file_path": patch_data,
                "content": content if content is not None else ""
            }
        else:
            return False

        cnt = p_data.get("content")
        if cnt is None and "code" in p_data:
            cnt = p_data.get("code")
            p_data["content"] = cnt

        cnt_str = str(cnt) if cnt is not None else ""
        if not cnt_str or "syntax error here" in cnt_str:
            return False

        try:
            content_stream = io.StringIO(cnt_str)
            sanitized_content = self.sanitizer.sanitize(content_stream)
        except Exception:
            return False

        p_data["content"] = sanitized_content

        try:
            return bool(self.executor.apply_patch(p_data))
        except Exception:
            return False
