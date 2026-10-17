import io
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from skills.git_inspector import GitInspector
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError


class TestPatchAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_repo_")
        self.analyzer = PatchAnalyzer()
        self.git_env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Integrator",
            "GIT_AUTHOR_EMAIL": "integrator@example.com",
            "GIT_COMMITTER_NAME": "Integrator",
            "GIT_COMMITTER_EMAIL": "integrator@example.com",
        }
        self._run_cmd(["git", "init"])
        self._run_cmd(["git", "config", "user.name", "Integrator"])
        self._run_cmd(["git", "config", "user.email", "integrator@example.com"])

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_cmd(self, cmd):
        result = subprocess.run(
            cmd,
            cwd=self.temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.git_env,
            check=True
        )
        return result.stdout

    def test_git_inspector_to_patch_analyzer_pipeline(self):
        filename = f"module_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.temp_dir, filename)
        rand_token_1 = uuid.uuid4().hex
        rand_token_2 = uuid.uuid4().hex

        initial_content = (
            f"# Header {rand_token_1}\n"
            "def calculate():\n"
            "    value = 10\n"
            "    return value\n"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        self._run_cmd(["git", "add", filename])
        self._run_cmd(["git", "commit", "-m", "Initial commit"])

        modified_content = (
            f"# Header {rand_token_1}\n"
            "def calculate():\n"
            "    # Modified logic\n"
            f"    tag = '{rand_token_2}'\n"
            "    value = 20\n"
            "    return value\n"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

        self._run_cmd(["git", "add", filename])
        self._run_cmd(["git", "commit", "-m", "Second commit"])

        head_commit = self._run_cmd(["git", "rev-parse", "HEAD"]).strip()

        inspector = GitInspector(self.temp_dir)
        diff_text = inspector.get_file_diff(head_commit)

        self.assertIn(filename, diff_text)
        self.assertIn(rand_token_2, diff_text)

        analysis = self.analyzer.analyze(diff_text)

        self.assertTrue(analysis["is_valid"])
        self.assertEqual(analysis["errors"], [])
        self.assertIn(filename, analysis["files"])

        stats = analysis["statistics"]
        self.assertEqual(stats["files_changed"], 1)
        self.assertEqual(stats["deletions"], 1)
        self.assertEqual(stats["additions"], 2)
        self.assertEqual(stats["total_changes"], 3)

        parsed = self.analyzer.parse(diff_text)
        self.assertEqual(len(parsed["files"]), 1)
        self.assertEqual(parsed["files"][0]["target_file"], filename)
        self.assertGreater(len(parsed["files"][0]["chunks"]), 0)

        chunk = parsed["files"][0]["chunks"][0]
        self.assertEqual(chunk["old_count"], 1)
        self.assertEqual(chunk["new_count"], 2)

    def test_syntax_risk_detection_from_live_patch(self):
        filename = f"danger_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.temp_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Safe code\n")

        self._run_cmd(["git", "add", filename])
        self._run_cmd(["git", "commit", "-m", "Base commit"])

        token = uuid.uuid4().hex
        injected_content = (
            "# Safe code\n"
            f"res = eval('{token}')\n"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(injected_content)

        self._run_cmd(["git", "add", filename])
        self._run_cmd(["git", "commit", "-m", "Risk commit"])

        commit_hash = self._run_cmd(["git", "rev-parse", "HEAD"]).strip()
        inspector = GitInspector(self.temp_dir)
        diff_text = inspector.get_file_diff(commit_hash)

        analysis = self.analyzer.analyze(diff_text)
        self.assertTrue(analysis["is_valid"])
        self.assertTrue(any(r["type"] == "dangerous_call" and "eval" in r["details"] for r in analysis["risks"]))

    def test_analyze_stream_and_file_io(self):
        filename = f"io_test_{uuid.uuid4().hex[:8]}.txt"
        unique_marker = f"marker_{uuid.uuid4().hex}"
        valid_diff = (
            f"--- a/{filename}\n"
            f"+++ b/{filename}\n"
            "@@ -1,1 +1,2 @@\n"
            " line1\n"
            f"+line2_{unique_marker}\n"
        )

        stream = io.StringIO(valid_diff)
        stream_result = self.analyzer.analyze_stream(stream)
        self.assertTrue(stream_result["is_valid"])
        self.assertEqual(stream_result["additions"], 1)
        self.assertEqual(stream_result["deletions"], 0)
        self.assertIn(filename, stream_result["files"])

        patch_file_path = os.path.join(self.temp_dir, f"patch_{uuid.uuid4().hex[:6]}.diff")
        with open(patch_file_path, "w", encoding="utf-8") as pf:
            pf.write(valid_diff)

        file_result = self.analyzer.analyze_file(patch_file_path)
        self.assertTrue(file_result["is_valid"])
        self.assertEqual(file_result["statistics"]["additions"], 1)
        self.assertIn(filename, file_result["files"])


if __name__ == "__main__":
    unittest.main()