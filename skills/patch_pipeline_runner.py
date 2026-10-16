import os
import io
from typing import Dict, Any, Union

from skills.code_validator import CodeValidator, CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError


class PatchPipelineRunnerError(Exception):
    """Базовое исключение для модуля PatchPipelineRunner."""
    pass


class PatchPipelineRunner:
    """Комбинирует валидатор кода и автокорректор патчей для безопасной конвейерной обработки."""

    def __init__(self, repo_path: str = None, validator=None, autocorrector=None):
        self.repo_path = repo_path
        self.validator = validator if validator is not None else CodeValidator(repo_path=repo_path)
        self.autocorrector = autocorrector if autocorrector is not None else PatchAutocorrector(
            repo_path=repo_path,
            validator=self.validator
        )

    def process_and_apply(self, file_name: str, code_fragment: str) -> bool:
        """Автоматически корректирует и валидирует фрагмент кода, затем сохраняет его в файл."""
        try:
            corrected_code = self.autocorrector.correct_and_validate(code_fragment)
            is_valid = self.validator.validate_code(corrected_code)
            if not is_valid:
                raise PatchPipelineRunnerError(f"Код не прошёл валидацию для файла {file_name}")
        except Exception as e:
            if isinstance(e, PatchPipelineRunnerError):
                raise e
            raise PatchPipelineRunnerError(f"Ошибка обработки патча: {e}") from e

        if self.repo_path:
            full_path = os.path.join(self.repo_path, file_name)
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(corrected_code)

        return True

    def run_pipeline(self, file_name: str, code_fragment: str) -> bool:
        """Интерфейсный метод запуска конвейера обработки и сохранения патча."""
        return self.process_and_apply(file_name, code_fragment)

    def process_stream(self, stream) -> bool:
        """Обрабатывает поток данных через автокорректор и валидатор."""
        try:
            transformed = self.autocorrector.transform_stream(stream)
            if isinstance(transformed, str):
                stream_input = io.BytesIO(transformed.encode('utf-8'))
            else:
                stream_input = transformed
            return self.validator.validate_stream(stream_input)
        except Exception as e:
            if isinstance(e, PatchPipelineRunnerError):
                raise e
            raise PatchPipelineRunnerError(f"Ошибка обработки потока: {e}") from e

    def batch_process(self, patches_dict: Dict[str, str]) -> Dict[str, Any]:
        """Пакетная обработка словаря патчей."""
        try:
            corrected_patches = self.autocorrector.batch_correct(patches_dict)
            return self.validator.batch_validate(corrected_patches)
        except Exception as e:
            if isinstance(e, PatchPipelineRunnerError):
                raise e
            raise PatchPipelineRunnerError(f"Ошибка пакетной обработки: {e}") from e


patch_pipeline_runner = PatchPipelineRunner
