import os
import shutil
import subprocess
import tempfile
import unittest
import uuid

from skills.git_inspector import GitInspector
from skills.patch_analyzer import PatchAnalyzer


class TestPatchAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, f"repo_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.repo_dir)

        subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "TestEngineer"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "engineer@test.local"], cwd=self.repo_dir, check=True)

        self.analyzer = PatchAnalyzer()
        self.inspector = GitInspector(self.repo_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _commit_file(self, filename: str, content: str, message: str) -> str:
        filepath = os.path.join(self.repo_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "add", filename], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=self.repo_dir, check=True, capture_output=True)
        rev = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return rev.stdout.strip()

    def test_clean_patch_analysis_from_git_inspector(self):
        file_token = uuid.uuid4().hex[:8]
        filename = f"module_{file_token}.py"
        base_var = f"var_{uuid.uuid4().hex[:6]}"
        initial_code = f"def compute_{file_token}():\n    {base_var} = 10\n    return {base_var}\n"

        self._commit_file(filename, initial_code, "Initial commit")

        add_token_1 = f"added_val_{uuid.uuid4().hex[:6]}"
        add_token_2 = f"added_val_{uuid.uuid4().hex[:6]}"
        modified_code = (
            f"def compute_{file_token}():\n"
            f"    {base_var} = 20\n"
            f"    {add_token_1} = 30\n"
            f"    {add_token_2} = {base_var} + {add_token_1}\n"
            f"    return {add_token_2}\n"
        )
        head_commit = self._commit_file(filename, modified_code, "Update logic")

        raw_diff = self.inspector.get_file_diff(head_commit)
        if isinstance(raw_diff, dict):
            diff_text = raw_diff.get("diff", str(raw_diff))
        else:
            diff_text = str(raw_diff)

        analysis = self.analyzer.analyze(diff_text)

        self.assertTrue(analysis["is_valid"])
        self.assertIn(filename, analysis["files"])
        self.assertGreaterEqual(analysis["additions"], 3)
        self.assertGreaterEqual(analysis["deletions"], 1)
        self.assertGreater(len(analysis["chunks"]), 0)
        self.assertEqual(len(analysis["syntax_risks"]), 0)

    def test_detects_syntax_risks_in_patch(self):
        file_token = uuid.uuid4().hex[:8]
        filename = f"danger_{file_token}.py"
        initial_code = f"def safe_func_{file_token}():\n    pass\n"
        self._commit_file(filename, initial_code, "Initial safe func")

        injected_token = uuid.uuid4().hex
        risky_code = (
            f"def safe_func_{file_token}():\n"
            f"    eval(f'dangerous_payload_{injected_token}')\n"
            f"    exec('x = 1')\n"
            f"    unclosed_tuple = (1, 2,\n"
        )
        head_commit = self._commit_file(filename, risky_code, "Introduce syntax risks")

        raw_diff = self.inspector.get_file_diff(head_commit)
        diff_text = raw_diff.get("diff", str(raw_diff)) if isinstance(raw_diff, dict) else str(raw_diff)

        analysis = self.analyzer.analyze(diff_text)

        self.assertTrue(analysis["is_valid"])
        self.assertIn(filename, analysis["files"])
        self.assertGreater(len(analysis["syntax_risks"]), 0)

        risk_descriptions = " ".join(
            str(risk.get("description", risk) if isinstance(risk, dict) else risk)
            for risk in analysis["syntax_risks"]
        )
        self.assertTrue(
            "eval" in risk_descriptions.lower()
            or "exec" in risk_descriptions.lower()
            or "syntax" in risk_descriptions.lower()
        )

    def test_malformed_chunk_structure_marks_patch_invalid(self):
        random_hash = uuid.uuid4().hex
        corrupted_patch = (
            f"--- a/broken_{random_hash}.py\n"
            f"+++ b/broken_{random_hash}.py\n"
            f"@@ invalid chunk header @@\n"
            f"+print('malformed {random_hash}')\n"
        )

        analysis = self.analyzer.analyze(corrupted_patch)

        self.assertFalse(analysis["is_valid"])
        self.assertGreater(len(analysis.get("errors", [])), 0)


if __name__ == "__main__":
    unittest.main()