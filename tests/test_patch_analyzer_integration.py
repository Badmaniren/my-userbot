import unittest
import uuid
import random
import tempfile
import os
import subprocess

from skills.patch_analyzer import PatchAnalyzer
from skills.git_inspector import GitInspector


class TestPatchAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Architect Bot"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "architect@system.local"], cwd=self.repo_path, capture_output=True, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_patch_analyzer_deep_integration(self):
        unique_file_name = f"secure_module_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.repo_path, unique_file_name)

        random_payload_id = random.randint(10000, 99999)
        vulnerable_content = f"# Payload ID: {random_payload_id}\nexec(input('Enter command: '))"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(vulnerable_content)

        subprocess.run(["git", "add", unique_file_name], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", f"Add unsafe code {random_payload_id}"], cwd=self.repo_path, capture_output=True, check=True)

        git_inspector = GitInspector(repo_path=self.repo_path)
        commit_history = git_inspector.get_commit_history(max_count=5)

        self.assertTrue(len(commit_history) > 0, "Git history must contain the initial commit.")
        latest_commit = commit_history[0]

        diff_data = git_inspector.get_file_diff(commit_hash=latest_commit if isinstance(latest_commit, str) else getattr(latest_commit, 'hash', str(latest_commit)))

        analyzer = PatchAnalyzer()

        analysis_result = analyzer.analyze(
            diff=diff_data,
            context={"payload_id": random_payload_id, "file": unique_file_name}
        )

        self.assertIsNotNone(analysis_result, "PatchAnalyzer returned None for real codebase diff.")

        result_str = str(analysis_result)
        self.assertIn(str(random_payload_id), result_str, "Analysis must process and reflect the dynamic payload identifier.")

        report_artifact_path = os.path.join(self.repo_path, f"security_report_{uuid.uuid4().hex}.json")
        if hasattr(analyzer, "export_report"):
            analyzer.export_report(report_artifact_path)
            self.assertTrue(os.path.exists(report_artifact_path), "Integration must successfully generate physical security report artifact.")


if __name__ == "__main__":
    unittest.main()