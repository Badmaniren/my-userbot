import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.patch_auto_remediator_pipeline import PatchAutoRemediatorPipeline
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_checker import PatchChecker, PatchCheckerError


class TestPatchAutoRemediatorPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        self.target_file_name = f"anti_cheat_module_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)
        
        self.original_code = "def secure_check():\n    return True\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.original_code)

        self.unique_signature = f"print('{uuid.uuid4().hex}')"
        self.patch_content = f"""diff --git a/ {self.target_file_name} b/{self.target_file_name}
--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -1,2 +1,3 @@
 def secure_check():
+    {self.unique_signature}
     return True
"""
        self.policy = {"allowed_risk_level": "low", "strict_mode": True}
        self.pipeline = PatchAutoRemediatorPipeline(repo_path=self.repo_path, policy=self.policy)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_integration_success_and_verification(self):
        analysis_result = self.pipeline.analyzer.analyze(self.patch_content)
        self.assertIsNotNone(analysis_result)

        check_result = self.pipeline.checker.check(
            patch_content=self.patch_content,
            repo_path=self.repo_path,
            target_file=self.target_file_name
        )
        self.assertIsInstance(check_result, dict)

        pipeline_result = self.pipeline.run_remediation_pipeline(
            patch_content=self.patch_content,
            target_file=self.target_file_name
        )

        self.assertIn("status", pipeline_result)
        self.assertTrue(pipeline_result.get("success", False))

        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(self.unique_signature, updated_content)

    def test_pipeline_integration_anti_cheat_security_block(self):
        malicious_signature = f"eval('os.system(\"rm -rf /\")') # {uuid.uuid4().hex}"
        malicious_patch = f"""diff --git a/ {self.target_file_name} b/{self.target_file_name}
--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -1,2 +1,3 @@
 def secure_check():
+    {malicious_signature}
     return True
"""
        with self.assertRaises((PatchAnalyzerError, PatchCheckerError, Exception)):
            self.pipeline.run_remediation_pipeline(
                patch_content=malicious_patch,
                target_file=self.target_file_name
            )


if __name__ == "__main__":
    unittest.main()