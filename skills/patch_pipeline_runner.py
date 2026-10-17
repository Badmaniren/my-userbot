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

            class PipelineResult(PatchEvaluationResult):
                def __init__(self, eval_res, history):
                    for attr in dir(eval_res):
                        if not attr.startswith('__'):
                            try:
                                setattr(self, attr, getattr(eval_res, attr))
                            except AttributeError:
                                pass
                    self._commit_history = history

                def get(self, key, default=None):
                    if key == "success":
                        return True
                    if key == "commit_history":
                        return self._commit_history
                    return getattr(self, key, default)

                def __getitem__(self, key):
                    if key == "success":
                        return True
                    if key == "commit_history":
                        return self._commit_history
                    if hasattr(self, key):
                        return getattr(self, key)
                    raise KeyError(key)

            commit_history = self.inspector.get_commit_history()
            return PipelineResult(evaluation_result, commit_history)

        except PatchPipelineError:
            raise
        except Exception as e:
            raise PatchPipelineError(str(e))