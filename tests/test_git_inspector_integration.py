import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.git_inspector import GitInspector

class TestGitInspectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.inspector = GitInspector(repo_path=self.test_dir)
        
        # Инициализируем git репозиторий через системные команды для честной интеграции
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Bot'")
        os.system(f"git -C {self.test_dir} config user.email 'test@bot.com'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_inspect_commit_history_and_changes(self):
        random_filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        random_content = f"content_{uuid.uuid4().hex}"
        random_commit_msg = f"commit_{uuid.uuid4().hex[:6]}"

        file_path = os.path.join(self.test_dir, random_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        os.system(f"git -C {self.test_dir} add {random_filename}")
        os.system(f"git -C {self.test_dir} commit -m '{random_commit_msg}'")

        history = self.inspector.get_history()
        
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        
        latest_commit = history[0]
        self.assertIn(random_commit_msg, str(latest_commit))

        changes = self.inspector.get_latest_changes()
        self.assertIn(random_filename, str(changes))
        self.assertIn(random_content, str(changes))

if __name__ == "__main__":
    unittest.main()