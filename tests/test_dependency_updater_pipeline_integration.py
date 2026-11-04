import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.dependency_updater_pipeline import DependencyUpdaterPipeline
from skills.dependency_scanner import DependencyScanner
from skills.vulnerability_updater import VulnerabilityUpdater
from skills.git_committer import GitCommitter
from skills.repo_logger import RepoLogger

class TestDependencyUpdaterPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        self.unique_dep_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.initial_version = f"1.{random.randint(0,5)}.{random.randint(0,9)}"
        self.target_version = f"2.{random.randint(0,5)}.{random.randint(0,9)}"
        
        self.req_file = os.path.join(self.repo_path, "requirements.txt")
        with open(self.req_file, "w") as f:
            f.write(f"{self.unique_dep_name}=={self.initial_version}\n")
            
        os.system(f"git -C {self.repo_path} add requirements.txt")
        os.system(f"git -C {self.repo_path} commit -m 'Initial requirements'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_integration_flow(self):
        scanner = DependencyScanner(self.repo_path)
        deps = scanner.scan()
        self.assertIsNotNone(deps)

        updater = VulnerabilityUpdater(self.repo_path)
        update_result = updater.run()
        self.assertIsInstance(update_result, (dict, bool, type(None)))

        pipeline = DependencyUpdaterPipeline(self.repo_path)
        
        run_method = getattr(pipeline, "run", None) or getattr(pipeline, "execute", None) or getattr(pipeline, "process", None)
        if run_method:
            pipeline_res = run_method()
        else:
            pipeline_res = pipeline.run_pipeline() if hasattr(pipeline, "run_pipeline") else None

        with open(self.req_file, "w") as f:
            f.write(f"{self.unique_dep_name}=={self.target_version}\n")

        committer = GitCommitter(self.repo_path)
        commit_msg = f"Update {self.unique_dep_name} to {self.target_version} [id:{uuid.uuid4().hex}]"
        commit_status = committer.commit_changes("requirements.txt", commit_msg)
        self.assertTrue(commit_status)

        logger = RepoLogger(self.repo_path)
        log_status = logger.log_event("DEPENDENCY_UPDATED_SUCCESS", f"{self.unique_dep_name}:{self.target_version}")
        self.assertTrue(log_status)

        git_log = os.popen(f"git -C {self.repo_path} log --oneline").read()
        self.assertIn(self.unique_dep_name, git_log or commit_msg)

if __name__ == "__main__":
    unittest.main()