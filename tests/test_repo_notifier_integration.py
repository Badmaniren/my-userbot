import os
import shutil
import subprocess
import tempfile
import unittest
import uuid

from skills.repo_notifier import RepoNotifier


class TestRepoNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_repo_notifier_")
        subprocess.run(
            ["git", "init", self.test_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", self.test_dir, "config", "user.name", f"Test_{uuid.uuid4().hex[:8]}"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", self.test_dir, "config", "user.email", f"{uuid.uuid4().hex[:8]}@example.com"],
            check=True,
            capture_output=True,
            text=True,
        )
        # Create an initial file and commit so repository has a valid HEAD
        init_file = os.path.join(self.test_dir, f"init_{uuid.uuid4().hex}.txt")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f"seed-content-{uuid.uuid4()}")
        subprocess.run(
            ["git", "-C", self.test_dir, "add", "."],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", self.test_dir, "commit", "-m", f"Initial commit {uuid.uuid4().hex}"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.notifier = RepoNotifier(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_notify_with_custom_path_creates_report_and_commits(self):
        random_suffix = uuid.uuid4().hex
        custom_report_path = os.path.join(self.test_dir, f"custom_report_{random_suffix}.txt")

        self.assertFalse(os.path.exists(custom_report_path))

        result = self.notifier.notify(custom_report_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(custom_report_path))
        self.assertGreater(os.path.getsize(custom_report_path), 0)

        with open(custom_report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIsInstance(content, str)
        self.assertTrue(len(content.strip()) > 0)

        git_log = subprocess.run(
            ["git", "-C", self.test_dir, "log", "--oneline"],
            check=True,
            capture_output=True,
            text=True,
        )
        log_lines = git_log.stdout.strip().splitlines()
        self.assertGreaterEqual(len(log_lines), 2)

    def test_notify_and_commit_default_path_creates_report(self):
        default_report_path = os.path.join(self.test_dir, "report.txt")
        if os.path.exists(default_report_path):
            os.remove(default_report_path)

        result = self.notifier.notify_and_commit()

        self.assertTrue(result)
        self.assertTrue(os.path.exists(default_report_path))
        self.assertGreater(os.path.getsize(default_report_path), 0)

        status_result = subprocess.run(
            ["git", "-C", self.test_dir, "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(status_result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()