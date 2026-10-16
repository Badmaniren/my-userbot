from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
from skills.patch_executor import PatchExecutor, PatchExecutorError

class PatchApplier:
    def __init__(self, repo_path_or_autocorrector=None, autocorrector=None, executor=None, repo_path=None):
        # Поддержка различных вариантов сигнатур инициализации:
        # 1. Юнит-тесты: PatchApplier(repo_path=..., autocorrector=..., executor=...)
        # 2. Интеграционные тесты: PatchApplier(autocorrector, executor)
        # 3. Позиционные вызовы: PatchApplier(repo_path, autocorrector, executor)

        if repo_path is not None:
            self.repo_path = repo_path
            self.autocorrector = autocorrector
            self.executor = executor
        elif autocorrector is not None and hasattr(repo_path_or_autocorrector, 'correct_syntax') and hasattr(autocorrector, 'apply_patch'):
            # Интеграционный тест: PatchApplier(autocorrector, executor)
            self.autocorrector = repo_path_or_autocorrector
            self.executor = autocorrector
            self.repo_path = getattr(self.autocorrector, 'repo_path', None) or getattr(self.executor, 'repo_path', None)
        elif repo_path_or_autocorrector is not None and hasattr(repo_path_or_autocorrector, 'correct_syntax') and executor is None:
            self.autocorrector = repo_path_or_autocorrector
            self.executor = autocorrector
            self.repo_path = getattr(self.autocorrector, 'repo_path', None)
        else:
            self.repo_path = repo_path_or_autocorrector
            self.autocorrector = autocorrector
            self.executor = executor

    def apply(self, raw_patch):
        corrected_patch = self.autocorrector.correct_syntax(raw_patch)
        return self.executor.apply_patch(corrected_patch)

    def process_stream(self, stream):
        transformed_data = self.autocorrector.transform_stream(stream)
        return self.executor.apply_patch(transformed_data)

    def rollback(self, file_path, commit_hash):
        return self.executor.rollback_patch(file_path, commit_hash)

    def apply_and_verify(self, patch_data):
        if isinstance(patch_data, dict):
            content = patch_data.get("content", "")
            corrected_content = self.autocorrector.correct_syntax(content)
            patch_data_copy = patch_data.copy()
            patch_data_copy["content"] = corrected_content
            if "file_path" not in patch_data_copy and "file_name" in patch_data_copy:
                patch_data_copy["file_path"] = patch_data_copy["file_name"]

            try:
                return self.executor.apply_patch(patch_data_copy)
            except PatchExecutorError:
                return self.executor.apply_patch(corrected_content)
        else:
            corrected_content = self.autocorrector.correct_syntax(patch_data)
            return self.executor.apply_patch(corrected_content)