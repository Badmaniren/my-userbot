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
        if not isinstance(patch_data, dict):
            raise PatchExecutorError("Invalid patch data format.")

        file_path = patch_data.get("file_path") or patch_data.get("file")
        content = patch_data.get("content")
        if not file_path or content is None:
            raise PatchExecutorError("Invalid patch data format.")

        file_path = str(file_path)
        
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

    def _parse_patches_from_text(self, text: str) -> list:
        if not text:
            return []
        import re

        patches = []
        file_match = re.search(r'(?:in|file:?)\s+([a-zA-Z0-9_\-\./]+\.py)', text, re.IGNORECASE)
        if not file_match:
            file_match = re.search(r'([a-zA-Z0-9_\-\./]+\.py)', text)

        if file_match:
            rel_file_path = file_match.group(1)
            full_path = os.path.join(self.repo_path, rel_file_path) if not os.path.isabs(rel_file_path) else rel_file_path

            existing_content = ""
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()
                except Exception:
                    existing_content = ""

            new_content = None
            change_match = re.search(r'change\s+(.+?)\s+to\s+(.+)', text, re.IGNORECASE)
            if change_match:
                old_str = change_match.group(1).strip()
                new_str = change_match.group(2).strip()
                if existing_content and old_str in existing_content:
                    new_content = existing_content.replace(old_str, new_str)
                elif existing_content:
                    new_content = existing_content + f"\n# {old_str} -> {new_str}\n"

            if new_content is None and "DIFF:" in text:
                diff_part = text.split("DIFF:", 1)[1].strip()
                if existing_content:
                    new_content = existing_content + f"\n# {diff_part}\n"
                else:
                    new_content = diff_part

            if new_content is not None:
                patches.append({
                    "file_path": rel_file_path,
                    "content": new_content
                })

        return patches

    def execute_from_lessons(self) -> dict:
        """Парсит гипотезы из уроков и выполняет их патчи."""
        if not self.lesson_parser:
            return {}

        import uuid
        hypotheses = self.lesson_parser.parse_lessons()
        results = {}

        for hyp in hypotheses:
            hyp_id = hyp.get("id") or hyp.get("commit") or uuid.uuid4().hex
            patches = hyp.get("patches", [])

            if not patches:
                content = hyp.get("content", "") or hyp.get("description", "")
                patches = self._parse_patches_from_text(content)

            success = True
            if patches:
                for patch in patches:
                    try:
                        self.apply_patch(patch)
                    except Exception:
                        success = False
            else:
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