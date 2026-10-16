"""
skills/code_patcher.py

Связывает валидацию кода с его применением: проверяет корректность структуры патча перед отправкой в исполнитель.
"""

from skills.code_validator import CodeValidator
from skills.patch_executor import PatchExecutor


class CodePatcherError(Exception):
    """Базовое исключение для ошибок CodePatcher."""
    pass


class CodePatcher:
    """Модуль для связывания валидации кода и его применения."""

    def __init__(self, repo_path=".", validator=None, executor=None):
        self.repo_path = repo_path
        self._validator = validator
        self._executor = executor

        if validator is None:
            CodeValidator(repo_path=self.repo_path)
        if executor is None:
            PatchExecutor(repo_path=self.repo_path)

    @property
    def validator(self):
        if self._validator is None:
            return CodeValidator(repo_path=self.repo_path)
        return self._validator

    @validator.setter
    def validator(self, value):
        self._validator = value

    @property
    def executor(self):
        if self._executor is None:
            return PatchExecutor(repo_path=self.repo_path)
        return self._executor

    @executor.setter
    def executor(self, value):
        self._executor = value

    def apply_patch(self, patch_data: dict) -> bool:
        """Валидирует AST и проверяет патч перед его отправкой в исполнитель."""
        if not isinstance(patch_data, dict):
            raise CodePatcherError("Patch data must be a dictionary.")

        code = patch_data.get("content")
        if code is None:
            code = patch_data.get("code")

        if code is not None:
            self.validator.validate_patch_ast(code)

        return self.executor.apply_patch(patch_data)

    def validate_and_apply(self, patch_data: dict) -> bool:
        """Алиас для применения патча после валидации."""
        return self.apply_patch(patch_data)

    def patch(self, patch_data: dict) -> bool:
        """Алиас для применения патча."""
        return self.apply_patch(patch_data)

    def __call__(self, patch_data: dict) -> bool:
        """Вызов объекта для применения патча."""
        return self.apply_patch(patch_data)

    def validate_stream(self, stream) -> bool:
        """Делегирует проверку потоковых данных валидатору."""
        res = self.validator.validate_stream(stream)
        if hasattr(stream, "read"):
            try:
                stream.read()
            except Exception:
                pass
        return res
