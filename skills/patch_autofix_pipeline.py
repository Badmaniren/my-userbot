from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError, PatchSyntaxError


class PatchAutofixPipelineError(Exception):
    """Исключение, возникающее при ошибках в конвейере автоматического исправления патчей."""
    pass


class PatchAutofixPipeline:
    """Конвейер автоматического исправления и верификации патчей путем объединения patch_evaluator и patch_autocorrector."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.evaluator = PatchEvaluator(repo_path)
        self.autocorrector = PatchAutocorrector(repo_path)

    def run(self, patch_content: str, target_file: str = None) -> PatchEvaluationResult:
        """Запускает процесс оценки патча. Если патч некорректен, пытается исправить синтаксис и выполнить оценку повторно."""
        eval_result = self.evaluator.evaluate(
            patch_content=patch_content,
            collect_telemetry=True,
            target_file=target_file
        )

        if not eval_result.is_valid or not eval_result.is_safe:
            try:
                corrected_content = self.autocorrector.correct_syntax(patch_content)
            except PatchSyntaxError as e:
                raise PatchAutofixPipelineError(str(e))
            except PatchAutocorrectorError as e:
                raise PatchAutofixPipelineError(str(e))

            eval_result = self.evaluator.evaluate(
                patch_content=corrected_content,
                collect_telemetry=True,
                target_file=target_file
            )

        return eval_result

    def run_stream(self, stream_data) -> PatchEvaluationResult:
        """Обрабатывает поток данных через конвейер автокоррекции и оценки."""
        transformed_stream = self.autocorrector.transform_stream(stream_data)
        return self.evaluator.evaluate_stream(transformed_stream)

    def run_batch(self, batch_dict: dict) -> dict:
        """Пакетная обработка патчей через автокорректор."""
        return self.autocorrector.batch_correct(batch_dict)


def patch_autofix_pipeline(repo_path: str, patch_content: str, target_file: str = None):
    """Функциональный интерфейс для быстрого запуска конвейера."""
    pipeline = PatchAutofixPipeline(repo_path)
    return pipeline.run(patch_content, target_file)