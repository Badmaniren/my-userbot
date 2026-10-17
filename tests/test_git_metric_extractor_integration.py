import os
import shutil
import subprocess
import tempfile
import unittest
import uuid

from skills.git_inspector import GitInspector
from skills.git_metric_extractor import GitMetricExtractor


class TestGitMetricExtractorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, f"repo_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.repo_path, exist_ok=True)

        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Architect Integrator"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "architect@integration.local"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _commit_file(self, filename: str, content: str, commit_message: str):
        filepath = os.path.join(self.repo_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(
            ["git", "add", filename],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_extract_metrics_with_git_inspector_integration(self):
        file1_name = f"service_{uuid.uuid4().hex[:6]}.py"
        file2_name = f"utils_{uuid.uuid4().hex[:6]}.py"
        random_token = uuid.uuid4().hex

        initial_content_file1 = f"# Header {random_token}\nline_1\nline_2\nline_3\n"
        self._commit_file(
            file1_name,
            initial_content_file1,
            f"feat: add {file1_name} with token {random_token}",
        )

        modified_content_file1 = f"# Header {random_token}\nline_1_modified\nline_4\n"
        self._commit_file(
            file1_name,
            modified_content_file1,
            f"refactor: modify {file1_name}",
        )

        initial_content_file2 = f"# Second file {uuid.uuid4().hex}\nalpha\nbeta\ngamma\n"
        self._commit_file(
            file2_name,
            initial_content_file2,
            f"feat: add {file2_name}",
        )

        inspector = GitInspector(repo_path=self.repo_path)
        extractor = GitMetricExtractor(git_inspector=inspector)

        metrics = extractor.extract_metrics(max_count=10)

        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics.get("total_commits"), 3)

        modified_files = metrics.get("modified_files", [])
        self.assertIn(file1_name, modified_files)
        self.assertIn(file2_name, modified_files)

        lines_added = metrics.get("lines_added", 0)
        lines_deleted = metrics.get("lines_deleted", 0)
        churn_rate = metrics.get("churn_rate", 0.0)

        self.assertGreater(lines_added, 0)
        self.assertGreater(lines_deleted, 0)
        self.assertGreater(churn_rate, 0.0)

        commit_metrics = metrics.get("commit_metrics", [])
        self.assertEqual(len(commit_metrics), 3)

        hashes = [c.get("commit_hash") for c in commit_metrics]
        self.assertEqual(len(set(hashes)), 3)
        for c in commit_metrics:
            self.assertIn("files_changed", c)
            self.assertIn("insertions", c)
            self.assertIn("deletions", c)

    def test_extract_metrics_instantiation_from_repo_path(self):
        file_name = f"config_{uuid.uuid4().hex[:6]}.json"
        content = f'{{"id": "{uuid.uuid4().hex}"}}\n'
        self._commit_file(file_name, content, f"chore: initial config {file_name}")

        extractor = GitMetricExtractor(repo_path=self.repo_path)
        metrics = extractor.extract_metrics(max_count=5)

        self.assertEqual(metrics.get("total_commits"), 1)
        self.assertIn(file_name, metrics.get("modified_files", []))
        self.assertGreater(metrics.get("lines_added", 0), 0)
        self.assertEqual(metrics.get("lines_deleted", 0), 0)
        self.assertIsInstance(metrics.get("churn_rate"), (int, float))


if __name__ == "__main__":
    unittest.main()