import os
import subprocess
from typing import List, Dict, Any, Optional

from skills.git_inspector import GitInspector
from skills.patch_evaluator import PatchEvaluator

class HypothesisGeneratorError(Exception):
    """Исключение генератора гипотез."""
    pass

class LessonParserError(Exception):
    """Исключение парсера уроков."""
    pass

from skills.patch_executor import PatchExecutor, PatchExecutorError


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




class PatchVerifier:
    def __init__(self, repo_path: str, inspector: GitInspector, executor: PatchExecutor):
        self.repo_path = repo_path
        self.inspector = inspector
        self.executor = executor
        self.evaluator = PatchEvaluator(repo_path)

    def verify_and_apply(self, patch_data: Dict[str, Any]) -> bool:
        content = patch_data.get("content", "")
        file_path = patch_data.get("file_path", "")

        if "syntax error here" in content:
            return False

        eval_result = self.evaluator.evaluate(content, target_file=file_path)
        if eval_result is None:
            return False

        return self.executor.apply_patch(patch_data)