import unittest
import tempfile
import os
import subprocess
import uuid
from skills.git_committer import GitCommitter

class TestGitCommitterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "init", self.repo_path], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Bot"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.local"], capture_output=True, check=True)
        
        self.committer = GitCommitter(self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_commit_all_with_random_message(self):
        random_file_name = f"file_{uuid.uuid4().hex}.txt"
        random_file_path = os.path.join(self.repo_path, random_file_name)
        random_content = uuid.uuid4().bytes
        
        with open(random_file_path, "wb") as f:
            f.write(random_content)

        random_message = f"feat: add random file {uuid.uuid4().hex}"
        
        success = self.committer.commit(random_message)
        self.assertTrue(success, "Метод commit должен успешно завершиться")

        log_result = subprocess.run(
            ["git", "-C", self.repo_path, "log", "-1", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(log_result.stdout.strip(), random_message)

    def test_integration_commit_changes_specific_file(self):
        target_file = f"tracked_{uuid.uuid4().hex}.txt"
        ignored_file = f"untracked_{uuid.uuid4().hex}.txt"
        
        with open(os.path.join(self.repo_path, target_file), "w") as f:
            f.write(str(uuid.uuid4()))
            
        with open(os.path.join(self.repo_path, ignored_file), "w") as f:
            f.write(str(uuid.uuid4()))

        random_message = f"fix: update specific file {uuid.uuid4().hex}"
        
        success = self.committer.commit_changes(target_file, random_message)
        self.assertTrue(success, "Метод commit_changes должен успешно закоммитить конкретный файл")

        status_result = subprocess.run(
            ["git", "-C", self.repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        self.assertIn(ignored_file, status_result.stdout, "Игнорируемый файл не должен быть в коммите")
        self.assertNotIn(target_file, status_result.stdout, "Закоммиченный файл должен отсутствовать в списке измененных")

    def test_subprocess_exception_handling_invalid_repo(self):
        invalid_committer = GitCommitter(os.path.join(self.repo_path, f"nonexistent_{uuid.uuid4().hex}"))
        random_message = f"chore: fail expected {uuid.uuid4().hex}"
        
        success_commit = invalid_committer.commit(random_message)
        self.assertFalse(success_commit, "commit должен вернуть False при невалидном пути к репозиторию")

        success_changes = invalid_committer.commit_changes("any_file.txt", random_message)
        self.assertFalse(success_changes, "commit_changes должен вернуть False при невалидном пути к репозиторию")

if __name__ == "__main__":
    unittest.main()