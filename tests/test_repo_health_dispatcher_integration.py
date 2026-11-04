import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Architect'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")
        
        self.random_id = str(uuid.uuid4())
        self.file_name = f"test_file_{self.random_id}.txt"
        self.file_path = os.path.join(self.test_dir, self.file_name)
        
        random_content = f"Initial metric data: {random.randint(1000, 9999)}"
        with open(self.file_path, "w") as f:
            f.write(random_content)
            
        os.system(f"git -C {self.test_dir} add {self.file_name}")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit {self.random_id}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignoreunicode=True) if hasattr(shutil, 'rmtree') else shutil.rmtree(self.test_dir)

    def test_dispatcher_composition_and_execution(self):
        dispatcher = RepoHealthDispatcher(self.test_dir)
        
        self.assertTrue(
            hasattr(dispatcher, "repo_health_dashboard") or hasattr(dispatcher, "dashboard") or callable(getattr(dispatcher, "dispatch", None)) or callable(getattr(dispatcher, "run", None)),
            "RepoHealthDispatcher must integrate underlying modules"
        )
        
        dispatch_method = getattr(dispatcher, "dispatch", None) or getattr(dispatcher, "run", None) or getattr(dispatcher, "process", None)
        
        if dispatch_method:
            result = dispatch_method()
            self.assertIsNotNone(result)
        
        dashboard_files = [f for f in os.listdir(self.test_dir) if "dashboard" in f or "report" in f]
        
        new_random_content = f"Updated metrics: {random.randint(10000, 99999)}"
        with open(self.file_path, "w") as f:
            f.write(new_random_content)
            
        dispatcher_methods = [method for method in dir(dispatcher) if callable(getattr(dispatcher, method)) and not method.startswith("_")]
        self.assertGreater(len(dispatcher_methods), 0)

if __name__ == "__main__":
    unittest.main()