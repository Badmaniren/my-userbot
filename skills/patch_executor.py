import os
import logging

logger = logging.getLogger("PatchExecutor")


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

    def _validate_patch(self, patch_data: dict) -> None:
        """Валидация патча перед применением для предотвращения деградации системы."""
        if not isinstance(patch_data, dict):
            raise PatchExecutorError("Invalid patch data: expected dictionary.")
        if "file_path" not in patch_data or "content" not in patch_data:
            raise PatchExecutorError("Invalid patch data format: missing required keys.")
        if not isinstance(patch_data["file_path"], str) or not isinstance(patch_data["content"], str):
            raise PatchExecutorError("Invalid patch data: 'file_path' and 'content' must be strings.")

    def apply_patch(self, patch_data: dict) -> bool:
        """Применяет один патч к файлу в репозитории с предварительной валидацией и атомарностью."""
        self._validate_patch(patch_data)

        file_path = patch_data["file_path"]
        content = patch_data["content"]
        
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            full_path = os.path.join(self.repo_path, file_path)

        logger.info(f"Applying patch to {full_path}")

        dir_name = os.path.dirname(full_path)
        temp_file_path = os.path.join(dir_name if dir_name else ".", f".tmp_{os.path.basename(full_path)}")

        try:
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            # Обеспечение атомарности записи через временный файл
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            os.replace(temp_file_path, full_path)
            logger.info(f"Successfully applied patch to {full_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply patch to {full_path}: {e}")
            raise PatchExecutorError(f"Failed to apply patch: {e}")
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to clean up temp file {temp_file_path}: {cleanup_err}")

    def execute_from_lessons(self) -> dict:
        """Парсит гипотезы из уроков и выполняет их патчи атомарно."""
        if not self.lesson_parser:
            logger.info("No lesson parser provided. Skipping execution from lessons.")
            return {}

        logger.info("Parsing lessons for hypotheses execution.")
        hypotheses = self.lesson_parser.parse_lessons()
        results = {}

        for hyp in hypotheses:
            hyp_id = hyp.get("id")
            patches = hyp.get("patches", [])
            success = True

            applied_patches = []
            logger.info(f"Executing hypothesis {hyp_id} with {len(patches)} patch(es).")
            for patch in patches:
                try:
                    self.apply_patch(patch)
                    applied_patches.append(patch)
                except Exception as patch_error:
                    success = False
                    logger.error(f"Error applying patch in hypothesis {hyp_id}: {patch_error}")
                    # Откат уже примененных в рамках данной гипотезы патчей при сбое
                    for applied in applied_patches:
                        fp = applied.get("file_path")
                        if self.git_inspector and fp:
                            try:
                                commit_hash = getattr(self.git_inspector, "current_commit", "HEAD")
                                self.rollback_patch(fp, commit_hash)
                            except Exception as rollback_error:
                                logger.error(f"Failed to rollback patch for {fp}: {rollback_error}")
                                raise PatchExecutorError(f"Rollback failed during recovery: {rollback_error}")
                    break

            results[hyp_id] = success

        return results

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        """Откатывает файл к состоянию на определенный коммит с помощью git_inspector."""
        if not self.git_inspector:
            logger.warning("Cannot rollback patch: git_inspector not provided.")
            return False

        try:
            logger.info(f"Rolling back {file_path} to commit {commit_hash}")
            original_content = self.git_inspector.read_file_at_commit(commit_hash, file_path)
            patch_data = {
                "file_path": file_path,
                "content": original_content,
                "mode": "overwrite"
            }
            return self.apply_patch(patch_data)
        except Exception as e:
            logger.error(f"Failed to rollback patch for {file_path}: {e}")
            raise PatchExecutorError(f"Failed to rollback patch: {e}")
