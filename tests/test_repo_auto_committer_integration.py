import unittest
import tempfile
import shutil
import os
import uuid
import random
from pathlib import Path

from skills.repo_auto_committer import RepoAutoCommitter


class TestRepoAutoCommitterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        os.system(f"git init -b main {self.repo_path} > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect' > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com' > /dev/null 2>&1")

        readme_path = os.path.join(self.repo_path, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("Initial commit")

        os.system(f"git -C {self.repo_path} add README.md > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit' > /dev/null 2>&1")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_auto_committer_pipeline_integration(self):
        random_file_name = f"feature_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Unique content UUID: {uuid.uuid4()}"

        file_path = os.path.join(self.repo_path, random_file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        auto_committer = RepoAutoCommitter(self.repo_path)

        result = auto_committer.run()

        self.assertTrue(
            result,
            "RepoAutoCommitter.run() должен вернуть True при успешном выполнении конвейера."
        )

        log_output = os.popen(f"git -C {self.repo_path} log -1 --pretty=format:'%s'").read()

        self.assertTrue(
            len(log_output.strip()) > 0,
            "Git коммит должен быть создан, но лог пуст."
        )

        status_output = os.popen(f"git -C {self.repo_path} status --porcelain").read()
        self.assertEqual(
            status_output.strip(),
            "",
            "В репозитории не должно оставаться не закоммиченных изменений после работы пайплайна."
        )


if __name__ == "__main__":
    unittest.main()