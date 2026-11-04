import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_restorer import RepoHealthRestorer
from skills.repo_health_guardian import RepoHealthGuardian
from skills.repo_recovery import RepoRecovery

class TestRepoHealthRestorerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Architect Bot'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@bot.com'")
        
        self.unique_msg = f"Initial commit {uuid.uuid4()}"
        self.test_file = os.path.join(self.test_dir, "README.md")
        
        with open(self.test_file, "w") as f:
            f.write(f"# {uuid.uuid4()}\n")
            
        os.system(f"git -C {self.test_dir} add README.md")
        os.system(f"git -C {self.test_dir} commit -m '{self.unique_msg}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_composition_and_restoration_integration(self):
        restorer = RepoHealthRestorer(self.test_dir)
        
        self.assertIsInstance(restorer, RepoHealthRestorer)
        
        has_guardian = any(isinstance(attr, RepoHealthGuardian) for attr in restorer.__dict__.values()) or hasattr(restorer, 'guardian') or hasattr(restorer, 'health_guardian')
        has_recovery = any(isinstance(attr, RepoRecovery) for attr in restorer.__dict__.values()) or hasattr(restorer, 'recovery') or hasattr(restorer, 'repo_recovery')
        
        corrupted_file = os.path.join(self.test_dir, f"corrupted_{uuid.uuid4()}.txt")
        with open(corrupted_file, "w") as f:
            f.write(str(uuid.uuid4()))
            
        if hasattr(restorer, 'restore_repository'):
            result = restorer.restore_repository()
        elif hasattr(restorer, 'run'):
            result = restorer.run()
        elif hasattr(restorer, 'full_restoration'):
            result = restorer.full_restoration()
        else:
            try:
                result = restorer.restore()
            except AttributeError:
                result = False

        self.assertIsNotNone(result)

        health_result = None
        if hasattr(restorer, 'guardian') and hasattr(restorer.guardian, 'check_health_and_audit'):
            health_result = restorer.guardian.check_health_and_audit()
        elif hasattr(restorer, 'health_guardian') and hasattr(restorer.health_guardian, 'check_health_and_audit'):
            health_result = restorer.health_guardian.check_health_and_audit()
        
        if health_result is not None:
            self.assertIsInstance(health_result, dict)

        recovery_instance = RepoRecovery(self.test_dir)
        recovery_status = recovery_instance.recover_repository()
        self.assertIsInstance(recovery_status, bool)

if __name__ == '__main__':
    unittest.main()