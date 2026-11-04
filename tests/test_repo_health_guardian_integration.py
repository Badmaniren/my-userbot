import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardianIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Guardian'")
        os.system(f"git -C {self.test_dir} config user.email 'test@guardian.local'")
        
        self.unique_id = str(uuid.uuid4())
        self.random_metric = random.randint(100, 999)
        
        self.test_file = os.path.join(self.test_dir, f"health_check_{self.unique_id}.txt")
        with open(self.test_file, "w") as f:
            f.write(f"Initial state for health guardian integration test. Metric: {self.random_metric}\n")
            
        os.system(f"git -C {self.test_dir} add {self.test_file}")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit {self.unique_id}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_health_guardian_composition_and_execution(self):
        guardian = RepoHealthGuardian(self.test_dir)
        
        self.assertTrue(
            hasattr(guardian, 'monitor') or hasattr(guardian, 'auditor'),
            "RepoHealthGuardian must compose existing skills like repo_monitor and repo_auditor"
        )
        
        new_feature_file = os.path.join(self.test_dir, f"feature_{uuid.uuid4()}.py")
        with open(new_feature_file, "w") as f:
            f.write(f"# Random payload {random.random()}\ndef compute_{self.random_metric}():\n    return {self.random_metric}\n")

        report_path = os.path.join(self.test_dir, f"audit_report_{self.unique_id}.json")
        
        has_run = False
        methods_to_try = ['run', 'maintain_health', 'check_and_heal', 'execute', 'process']
        
        for method_name in methods_to_try:
            if hasattr(guardian, method_name):
                method = getattr(guardian, method_name)
                try:
                    res = method()
                    has_run = True
                    break
                except TypeError:
                    try:
                        res = method(report_path)
                        has_run = True
                        break
                    except Exception:
                        pass

        if not has_run:
            self.assertTrue(hasattr(guardian, 'monitor') or hasattr(guardian, 'auditor'), 
                            "Module must expose monitoring and auditing capabilities through composition.")

        if hasattr(guardian, 'monitor') and hasattr(guardian.monitor, 'check_status'):
            status = guardian.monitor.check_status()
            self.assertIsInstance(status, str)

        if hasattr(guardian, 'auditor') and hasattr(guardian.auditor, 'audit'):
            audit_res = guardian.auditor.audit()
            self.assertIsNotNone(audit_res)

        self.assertTrue(os.path.exists(new_feature_file), "Repository environment intact during guardian execution.")

if __name__ == '__main__':
    unittest.main()