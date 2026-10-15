import os


class PatchExecutorError(Exception):
    """Кастомное исключение для ошибок PatchExecutor."""
    pass


class PatchExecutor:
    """Модуль для автоматического применения патчей и выполнения гипотез."""

    def __init__(self, repo_path=None, git_inspector=None, lesson_parser=None):
        if repo_path is None and git_inspector is not None and hasattr(git_inspector, "repo_path"):
            repo_path = git_inspector.repo_path
        
        self.repo_path = repo_path or "."
        self.git_inspector = git_inspector
        self.lesson_parser = lesson_parser

    def apply_patch(self, patch_data: dict) -> bool:
        """Применяет один патч к файлу в репозитории."""
        if not isinstance(patch_data, dict) or "file_path" not in patch_data or "content" not in patch_data:
            raise PatchExecutorError("Invalid patch data format.")

        file_path = patch_data["file_path"]
        content = patch_data["content"]
        
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.repo_path, file_path)

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            raise PatchExecutorError(f"Failed to apply patch: {e}")

    def execute_from_lessons(self) -> dict:
        """Парсит гипотезы из уроков и выполняет их патчи."""
        if not self.lesson_parser:
            return {}

        hypotheses = self.lesson_parser.parse_lessons()
        results = {}

        for hyp in hypotheses:
            hyp_id = hyp.get("id")
            patches = hyp.get("patches", [])
            success = True
            for patch in patches:
                try:
                    self.apply_patch(patch)
                except Exception:
                    success = False
            results[hyp_id] = success

        return results

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        """Откатывает файл к состоянию на определенный коммит с помощью git_inspector."""
        if not self.git_inspector:
            return False

        try:
            original_content = self.git_inspector.read_file_at_commit(commit_hash, file_path)
            patch_data = {
                "file_path": file_path,
                "content": original_content,
                "mode": "overwrite"
            }
            return self.apply_patch(patch_data)
        except Exception as e:
            raise PatchExecutorError(f"Failed to rollback patch: {e}")