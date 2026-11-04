import unittest
import tempfile
import shutil
import os
import uuid
import subprocess
from skills.changelog_generator import ChangelogGenerator
from skills.git_committer import GitCommitter

class TestChangelogGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test Architect"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True)
        
        self.random_id = str(uuid.uuid4())
        self.file_name = f"feature_{self.random_id}.txt"
        self.file_path = os.path.join(self.test_dir, self.file_name)
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(f"Initial content {self.random_id}\n")
            
        committer = GitCommitter(self.test_dir)
        committer.commit_changes(self.file_name, f"feat: add new feature {self.random_id}")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_changelog_generation_integration(self):
        generator = ChangelogGenerator(self.test_dir)
        
        methods = [m for m in dir(generator) if callable(getattr(generator, m)) and not m.startswith("_")]
        
        changelog_content = None
        for method_name in methods:
            method = getattr(generator, method_name)
            try:
                result = method()
                if isinstance(result, str) and self.random_id in result:
                    changelog_content = result
                    break
                elif isinstance(result, dict):
                    combined = str(result)
                    if self.random_id in combined:
                        changelog_content = combined
                        break
            except TypeError:
                continue

        if not changelog_content:
            for method_name in methods:
                method = getattr(generator, method_name)
                try:
                    result = method(os.path.join(self.test_dir, f"CHANGELOG_{self.random_id}.md"))
                    if isinstance(result, str) and self.random_id in result:
                        changelog_content = result
                        break
                except Exception:
                    continue

        self.assertIsNotNone(changelog_content, "Changelog generator failed to include real git history data.")
        self.assertIn(self.random_id, changelog_content, "Generated changelog does not contain the expected random commit message signature.")

if __name__ == "__main__":
    unittest.main()