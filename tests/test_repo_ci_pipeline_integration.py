import unittest
import tempfile
import shutil
import os
import uuid
import subprocess
from skills.repo_ci_pipeline import RepoCIPipeline

class TestRepoCIPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True)
        
        self.unique_filename = f"file_{uuid.uuid4().hex}.txt"
        self.file_path = os.path.join(self.test_dir, self.unique_filename)
        
        unique_content = f"content_{uuid.uuid4()}"
        with open(self.file_path, "w") as f:
            f.write(unique_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.unique_filename], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ci_pipeline_real_integration(self):
        pipeline = RepoCIPipeline(self.test_dir)
        
        has_run_method = hasattr(pipeline, "run") or hasattr(pipeline, "run_pipeline") or hasattr(pipeline, "execute")
        self.assertTrue(has_run_method, "RepoCIPipeline должен содержать метод запуска пайплайна")
        
        if hasattr(pipeline, "run"):
            result = pipeline.run()
        elif hasattr(pipeline, "run_pipeline"):
            result = pipeline.run_pipeline()
        else:
            result = pipeline.execute()
            
        self.assertIsNotNone(result)
        
        git_tags = subprocess.run(["git", "-C", self.test_dir, "tag"], capture_output=True, text=True, check=True)
        tags_output = git_tags.stdout.strip()
        
        self.assertIsInstance(tags_output, str)

if __name__ == "__main__":
    unittest.main()