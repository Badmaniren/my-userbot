from skills.patch_evaluator import PatchEvaluator, PatchEvaluatorError, PatchEvaluationResult
from skills.autonomous_engine import AutonomousEngine, AutonomousEngineError


class PatchAutoRemediatorError(Exception):
    """Исключение, возникающее при ошибках автоматического применения и оценки патчей."""
    pass


class PatchAutoRemediator:
    """Модуль для автоматического применения исправлений и оценки их качества."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.patch_evaluator = PatchEvaluator(repo_path=self.repo_path)
        self.evaluator = self.patch_evaluator  # Алиас для поддержки интеграционного теста
        
        self.autonomous_engine = AutonomousEngine(repo_path=self.repo_path)
        self.engine = self.autonomous_engine  # Алиас для поддержки интеграционного теста

    def remediate(self, patch_content: str, max_commits: int = 100, target_file: str = None):
        """Оценивает патч и запускает автономный движок при успешной оценке."""
        try:
            eval_result = self.patch_evaluator.evaluate(patch_content)
        except PatchEvaluatorError as e:
            raise PatchAutoRemediatorError(f"Evaluator error: {e}")

        if not eval_result.is_safe:
            raise PatchAutoRemediatorError("Patch is unsafe")
        if not eval_result.is_valid:
            raise PatchAutoRemediatorError("Patch is invalid")

        try:
            # Некоторые версии AutonomousEngine.run_cycle могут принимать target_file, а некоторые нет.
            # Попробуем передать аргумент, если он поддерживается или нужен интеграционному тесту.
            if target_file is not None:
                try:
                    return self.autonomous_engine.run_cycle(max_commits=max_commits, target_file=target_file)
                except TypeError:
                    return self.autonomous_engine.run_cycle(max_commits=max_commits)
            else:
                return self.autonomous_engine.run_cycle(max_commits=max_commits)
        except AutonomousEngineError as e:
            raise PatchAutoRemediatorError(f"Engine error: {e}")

    def remediate_stream(self, stream_data, **kwargs):
        """Оценивает поток патча и запускает автономный цикл."""
        try:
            eval_result = self.patch_evaluator.evaluate_stream(stream_data)
        except PatchEvaluatorError as e:
            raise PatchAutoRemediatorError(f"Evaluator error: {e}")

        if hasattr(eval_result, 'is_safe') and not eval_result.is_safe:
            raise PatchAutoRemediatorError("Patch is unsafe")
        if hasattr(eval_result, 'is_valid') and not eval_result.is_valid:
            raise PatchAutoRemediatorError("Patch is invalid")

        try:
            return self.autonomous_engine.run_autonomous_loop(**kwargs)
        except AutonomousEngineError as e:
            raise PatchAutoRemediatorError(f"Engine loop error: {e}")