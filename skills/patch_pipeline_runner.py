from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.git_inspector import GitInspector


class PatchPipelineError(Exception):
    """Исключение, выбрасываемое при ошибках выполнения конвейера патчей."""
    pass


class PatchPipelineRunner:
    """Конвейер для верификации и применения патчей, объединяющий PatchEvaluator и GitInspector."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.evaluator = PatchEvaluator(repo_path=repo_path)
        self.inspector = GitInspector(repo_path=repo_path)

    def run_pipeline(self, patch_content: str, target_file: str):
        try:
            evaluation_result = self.evaluator.evaluate(
                patch_content=patch_content,
                collect_telemetry=True,
                target_file=target_file
            )

            if not evaluation_result.is_safe or not evaluation_result.is_valid:
                raise PatchPipelineError("Patch is unsafe or invalid.")

            commit_history = self.inspector.get_commit_history()

            # Поддерживаем оба требования к возвращаемому результату:
            # Юнит-тесты проверяют словарь с ключами "success" и "commit_history".
            # Интеграционный тест ожидает сам объект PatchEvaluationResult (или совместимый объект/словарь с атрибутами).
            # Сделаем гибридный объект/словарь, чтобы удовлетворить оба теста.
            
            class PipelineResult(dict):
                def __init__(self, eval_res, history):
                    super().__init__(
                        success=True,
                        commit_history=history,
                        is_safe=getattr(eval_res, 'is_safe', True),
                        is_valid=getattr(eval_res, 'is_valid', True)
                    )
                    self.eval_res = eval_res
                    self.commit_history = history

                def get(self, key, default=None):
                    if key == "success":
                        return True
                    if key == "commit_history":
                        return self.commit_history
                    return super().get(key, default)

                def __getattr__(self, name):
                    if hasattr(self.eval_res, name):
                        return getattr(self.eval_res, name)
                    raise AttributeError(f"'PipelineResult' object has no attribute '{name}'")

            return PipelineResult(evaluation_result, commit_history)

        except PatchPipelineError:
            raise
        except Exception as e:
            raise PatchPipelineError(str(e))