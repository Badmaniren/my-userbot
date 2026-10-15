from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError
from skills.patch_executor import PatchExecutor, PatchExecutorError


class AutonomousEngineError(Exception):
    """Базовое исключение для AutonomousEngine."""
    pass


class AutonomousEngine:
    def __init__(
        self,
        repo_path=None,
        git_inspector=None,
        lesson_parser=None,
        hypothesis_generator=None,
        patch_executor=None
    ):
        self.repo_path = repo_path
        self.git_inspector = git_inspector if git_inspector is not None else GitInspector(repo_path=self.repo_path)
        self.lesson_parser = lesson_parser if lesson_parser is not None else LessonParser(git_inspector=self.git_inspector)
        self.hypothesis_generator = hypothesis_generator if hypothesis_generator is not None else HypothesisGenerator(
            git_inspector=self.git_inspector, lesson_parser=self.lesson_parser
        )
        self.patch_executor = patch_executor if patch_executor is not None else PatchExecutor(
            repo_path=self.repo_path, git_inspector=self.git_inspector, lesson_parser=self.lesson_parser
        )

    def run_autonomous_cycle(self, max_commits=10):
        try:
            hypotheses = self.hypothesis_generator.generate_hypotheses(max_commits)
            prioritized = self.hypothesis_generator.prioritize_hypotheses(hypotheses)
            for h in prioritized:
                try:
                    self.patch_executor.apply_patch(h)
                except PatchExecutorError:
                    if isinstance(h, dict) and "file" in h and "content" in h:
                        raise
                    # Если формат гипотезы не подходит для прямого применения патча, пропускаем ее
                    continue
            result = self.patch_executor.execute_from_lessons()
            return result
        except HypothesisGeneratorError as e:
            raise AutonomousEngineError(str(e)) from e
        except PatchExecutorError as e:
            raise AutonomousEngineError(str(e)) from e

    def apply_specific_patch(self, patch_data):
        return self.patch_executor.apply_patch(patch_data)

    def rollback_latest_patch(self, file_path=None, commit_hash=None):
        return self.patch_executor.rollback_patch(file_path, commit_hash)

    def run_cycle(self):
        return self.run_autonomous_cycle()

    def execute(self):
        return self.run_autonomous_cycle()

    def analyze_and_fix(self):
        return self.run_autonomous_cycle()