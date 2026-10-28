import os
import sys
import subprocess
import tempfile
import unittest
import uuid
import random

from skills import patch_analyzer
from skills.git_inspector import GitInspector


class TestPatchAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self._run_git(["init"])
        self._run_git(["config", "user.name", "TestUser"])
        self._run_git(["config", "user.email", "test@example.com"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_git(self, args):
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        return result.stdout

    def test_patch_analyzer_with_git_inspector(self):
        file_name_1 = f"feature_{uuid.uuid4().hex[:8]}.py"
        file_name_2 = f"config_{uuid.uuid4().hex[:8]}.json"

        path_1 = os.path.join(self.repo_path, file_name_1)
        path_2 = os.path.join(self.repo_path, file_name_2)

        unique_base_id = uuid.uuid4().hex
        base_lines = [f"def base_func_{unique_base_id}_{i}(): pass" for i in range(4)]
        with open(path_1, "w", encoding="utf-8") as f:
            f.write("\n".join(base_lines) + "\n")

        self._run_git(["add", "."])
        self._run_git(["commit", "-m", "Initial setup"])

        unique_added_id = uuid.uuid4().hex
        num_added = random.randint(3, 7)
        added_lines = [f"# Dynamic line {unique_added_id}_{i}" for i in range(num_added)]
        
        modified_lines = base_lines[:1] + added_lines + base_lines[2:]
        with open(path_1, "w", encoding="utf-8") as f:
            f.write("\n".join(modified_lines) + "\n")

        config_data = f'{{"id": "{uuid.uuid4().hex}", "status": "active"}}'
        with open(path_2, "w", encoding="utf-8") as f:
            f.write(config_data + "\n")

        self._run_git(["add", "."])

        raw_patch = self._run_git(["diff", "--cached"])

        inspector = GitInspector(self.repo_path)
        self.assertTrue(os.path.exists(self.repo_path))

        if hasattr(patch_analyzer, "PatchAnalyzer"):
            analyzer = patch_analyzer.PatchAnalyzer()
        else:
            analyzer = patch_analyzer

        if hasattr(analyzer, "analyze_patch"):
            analysis_result = analyzer.analyze_patch(raw_patch)
        elif hasattr(analyzer, "analyze"):
            analysis_result = analyzer.analyze(raw_patch)
        elif hasattr(analyzer, "analyze_diff"):
            analysis_result = analyzer.analyze_diff(raw_patch)
        elif callable(analyzer):
            analysis_result = analyzer(raw_patch)
        else:
            self.fail("No suitable analysis method found in patch_analyzer module")

        self.assertIsNotNone(analysis_result)

        if isinstance(analysis_result, dict):
            files = analysis_result.get("affected_files", analysis_result.get("files", []))
            if files:
                filenames = [str(f) for f in files]
                self.assertTrue(any(file_name_1 in fn for fn in filenames))
                self.assertTrue(any(file_name_2 in fn for fn in filenames))

            additions = analysis_result.get("added_lines", analysis_result.get("additions", None))
            if additions is not None:
                self.assertGreaterEqual(additions, num_added)

            deletions = analysis_result.get("deleted_lines", analysis_result.get("deletions", None))
            if deletions is not None:
                self.assertGreaterEqual(deletions, 1)

            complexity = analysis_result.get("complexity", analysis_result.get("diff_complexity", None))
            if complexity is not None:
                self.assertIsInstance(complexity, (int, float))


if __name__ == "__main__":
    unittest.main()