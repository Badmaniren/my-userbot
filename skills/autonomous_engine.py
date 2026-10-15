from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor


class AutonomousEngine:
    def __init__(
        self,
        repo_path=None,
        git_inspector=None,
        lesson_parser=None,
        hypothesis_generator=None,
        patch_executor=None,
    ):
        self.repo_path = repo_path
        self._git_inspector = git_inspector
        self._lesson_parser = lesson_parser
        self._hypothesis_generator = hypothesis_generator
        self._patch_executor = patch_executor

    @property
    def git_inspector(self):
        if self._git_inspector is None:
            self._git_inspector = GitInspector(self.repo_path) if self.repo_path else GitInspector()
        return self._git_inspector

    @git_inspector.setter
    def git_inspector(self, value):
        self._git_inspector = value

    @property
    def lesson_parser(self):
        if self._lesson_parser is None:
            self._lesson_parser = LessonParser(self.git_inspector)
        return self._lesson_parser

    @lesson_parser.setter
    def lesson_parser(self, value):
        self._lesson_parser = value

    @property
    def hypothesis_generator(self):
        if self._hypothesis_generator is None:
            self._hypothesis_generator = HypothesisGenerator(self.git_inspector, self.lesson_parser)
        return self._hypothesis_generator

    @hypothesis_generator.setter
    def hypothesis_generator(self, value):
        self._hypothesis_generator = value

    @property
    def patch_executor(self):
        if self._patch_executor is None:
            self._patch_executor = PatchExecutor()
        return self._patch_executor

    @patch_executor.setter
    def patch_executor(self, value):
        self._patch_executor = value

    def run_cycle(self, max_commits=10):
        hypotheses = self.hypothesis_generator.generate_hypotheses(max_commits)
        prioritized = self.hypothesis_generator.prioritize_hypotheses(hypotheses)

        applied_results = []
        for hyp in prioritized:
            try:
                res = self.patch_executor.apply_patch(hyp)
            except Exception:
                res = False
            applied_results.append(res)

        return {
            "status": "success",
            "hypotheses": prioritized,
            "applied": applied_results
        }

    def execute_lessons_cycle(self):
        return self.patch_executor.execute_from_lessons()

    def inspect_file_content(self, commit_hash, file_path):
        return self.git_inspector.read_file_at_commit(commit_hash, file_path)

    def run_autonomous_cycle(self, max_commits=10):
        hypotheses = self.hypothesis_generator.generate_hypotheses(max_commits)
        prioritized = self.hypothesis_generator.prioritize_hypotheses(hypotheses)

        applied_patches = []
        for hyp in prioritized:
            try:
                res = self.patch_executor.apply_patch(hyp)
            except Exception:
                res = False
            applied_patches.append(res)

        return {
            "status": "success",
            "applied_patches": applied_patches
        }
