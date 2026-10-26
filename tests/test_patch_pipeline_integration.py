import unittest
import uuid
import random
import os
import tempfile
from skills.patch_pipeline import PatchPipeline
from skills.code_validator import CodeValidator
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_autocorrector import PatchAutocorrector
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.git_inspector import GitInspector

class TestPatchPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, "audit.log")

        self.random_id = str(uuid.uuid4())
        self.random_metric_val = random.randint(100, 999)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=50
        )
        self.code_validator = CodeValidator(repo_path=self.repo_path)
        self.patch_analyzer = PatchAnalyzer()
        self.patch_autocorrector = PatchAutocorrector(repo_path=self.repo_path)
        self.git_inspector = GitInspector(repo_path=self.repo_path)

        self.pipeline = PatchPipeline(
            audit_hub=self.audit_hub,
            validator=self.code_validator,
            analyzer=self.patch_analyzer,
            autocorrector=self.patch_autocorrector,
            git_inspector=self.git_inspector
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_pipeline_integration_flow(self):
        dummy_file_name = f"module_{self.random_id}.py"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)

        broken_code = f"def compute_{self.random_id}():\n    return {self.random_metric_val} + 'string_mismatch'\n"

        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(broken_code)

        patch_content = f"""
--- a/{dummy_file_name}
+++ b/{dummy_file_name}
@@ -1,2 +1,2 @@
 def compute_{self.random_id}():
-    return {self.random_metric_val} + 'string_mismatch'
+    return {self.random_metric_val}
"""

        pipeline_result = self.pipeline.process_patch(
            patch_data=patch_content,
            target_file=dummy_file_name,
            session_id=self.random_id
        )

        self.assertIsNotNone(pipeline_result, "Конвейер не должен возвращать None")
        self.assertTrue(
            pipeline_result.get("success", False),
            f"Патч-конвейер завершился с ошибкой: {pipeline_result}"
        )

        self.assertEqual(
            pipeline_result.get("applied_session_id"),
            self.random_id,
            "Идентификатор сессии в результате должен совпадать со сгенерированным"
        )

        with open(dummy_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(
            str(self.random_metric_val),
            updated_content,
            "Целевой файл должен содержать исправленные данные"
        )
        self.assertNotIn(
            "string_mismatch",
            updated_content,
            "Ошибочный код должен быть полностью удален из файла"
        )

        report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(report, "Аудит-хаб должен сформировать итоговый отчет")

if __name__ == "__main__":
    unittest.main()