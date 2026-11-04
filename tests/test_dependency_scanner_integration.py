import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.dependency_scanner import DependencyScanner
from skills.repo_logger import RepoLogger
from skills.git_committer import GitCommitter


class TestDependencyScannerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        os.system(f"git init -b main {self.repo_path} > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.name 'Arch Test' > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.email 'arch@test.com' > /dev/null 2>&1")

        self.unique_dep_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.unique_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dependency_scanner_end_to_end_integration(self):
        req_content = f"{self.unique_dep_name}=={self.unique_version}\n"
        req_path = os.path.join(self.repo_path, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(req_content)

        committer = GitCommitter(self.repo_path)
        commit_success = committer.commit_changes("requirements.txt", f"Add {self.unique_dep_name}")
        self.assertTrue(commit_success, "GitCommitter failed to commit requirements.txt")

        logger = RepoLogger(self.repo_path)
        log_success = logger.log_event("dependency_added", {"package": self.unique_dep_name, "version": self.unique_version})
        self.assertTrue(log_success, "RepoLogger failed to log the dependency event")

        scanner = DependencyScanner(self.repo_path)
        
        scan_results = None
        for method_name in ["scan", "parse_dependencies", "detect_dependencies", "run", "process_dependencies"]:
            if hasattr(scanner, method_name):
                scan_results = getattr(scanner, method_name)()
                break
        
        if scan_results is None and hasattr(scanner, "__call__"):
            scan_results = scanner()

        self.assertIsNotNone(scan_results, "DependencyScanner did not return any results")

        results_str = str(scan_results)
        self.assertIn(self.unique_dep_name, results_str, f"Scanned results did not contain the dynamically generated package name: {self.unique_dep_name}")
        self.assertIn(self.unique_version, results_str, f"Scanned results did not contain the dynamically generated version: {self.unique_version}")

        git_status = os.popen(f"git -C {self.repo_path} status --porcelain").read()
        self.assertEqual(git_status.strip(), "", "Repository working tree is not clean after commit and scan")


if __name__ == "__main__":
    unittest.main()