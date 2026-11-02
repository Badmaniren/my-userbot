import unittest
import uuid
import random
import os
import tempfile

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError, analyze
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.git_inspector import GitInspector


class TestPatchAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, "audit.log")
        
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=0.5)
        self.analyzer = PatchAnalyzer()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_analyzer_full_pipeline_integration(self):
        rand_id = str(uuid.uuid4())[:8]
        filename = f"module_{rand_id}.py"
        added_content_line = f"# Unique validation marker {uuid.uuid4()}"
        removed_content_line = f"# Old deprecated marker {uuid.uuid4()}"

        raw_patch = f"""diff --git a/dev/null b/{filename}
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/{filename}
@@ -0,0 +1 @@
+{added_content_line}
diff --git a/old_module.py b/old_module.py
deleted file mode 100644
index 7654321..0000000
--- a/old_module.py
+++ /dev/null
@@ -1 +0,0
-{removed_content_line}
"""

        analysis_result = self.analyzer.analyze(raw_patch)

        self.assertIn(filename, analysis_result["new_files"])
        self.assertIn("old_module.py", analysis_result["deleted_files"])
        self.assertIn(filename, analysis_result["affected_files"])
        self.assertGreaterEqual(analysis_result["total_added"], 1)
        self.assertGreaterEqual(analysis_result["total_removed"], 1)

        self.audit_hub.log_anomaly(
            source="patch_analyzer",
            severity="INFO",
            details=f"Analyzed patch with complexity {analysis_result['complexity']}",
            telemetry_snapshot={"added_lines": analysis_result["total_added"]}
        )

        history = self.git_inspector.get_history()
        self.assertIsInstance(history, (list, dict, type(None)))

        report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(report)

        func_result = analyze(raw_patch)
        self.assertEqual(func_result["total_added"], analysis_result["total_added"])
        self.assertEqual(func_result["total_removed"], analysis_result["total_removed"])


if __name__ == "__main__":
    unittest.main()