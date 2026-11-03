import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_monitor import RepoMonitor
from skills.git_committer import GitCommitter

class TestRepoMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git init {self.test_dir} -b main > /dev/null 2>&1")
        os.system(f"git -C {self.test_dir} config user.name 'Test Bot'")
        os.system(f"git -C {self.test_dir} config user.email 'bot@test.com'")
        
        self.monitor = RepoMonitor(self.test_dir)
        self.committer = GitCommitter(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repo_monitor_and_committer_flow(self):
        random_id = str(uuid.uuid4())
        file_name = f"file_{random.randint(1000, 9999)}.txt"
        file_path = os.path.join(self.test_dir, file_name)
        
        content = f"Random test content: {random_id}"
        with open(file_path, "w") as f:
            f.write(content)

        status_before = self.monitor.check_status()
        self.assertIn(file_name, str(status_before))

        commit_message = f"Add test file {random_id}"
        success = self.committer.commit_changes(file_path, commit_message)
        self.assertTrue(success)

        status_after = self.monitor.check_status()
        self.assertNotIn(file_name, str(status_after))

        log_output = os.popen(f"git -C {self.test_dir} log -1 --pretty=format:'%s'").read()
        self.assertIn(commit_message, log_output)

if __name__ == "__main__":
    unittest.main()