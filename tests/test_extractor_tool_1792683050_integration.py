import unittest
import uuid
import random
import os
import tempfile
from skills.extractor_tool_1792683050 import ExtractorTool
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestIntegrationExtractorToolAndAuditor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extractor_integration_with_audit_pipeline(self):
        unique_id = str(uuid.uuid4())
        severity_level = random.choice(["INFO", "WARNING", "CRITICAL"])

        markup_snippet = f'<metadata id="{unique_id}" status="active" value="{random.randint(1, 1000)}" />'

        extractor = ExtractorTool()
        extracted_data = extractor.extract(markup_snippet)

        self.assertIn(unique_id, str(extracted_data))

        audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.uniform(0.5, 0.9)
        )

        audit_hub.log_anomaly(
            source="extractor_tool_1792683050",
            severity=severity_level,
            details={"message": f"Extracted metadata successfully for token {unique_id}"},
            telemetry_snapshot={"extracted_keys": list(extracted_data.keys())}
        )

        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.random() * 100
        audit_hub.aggregate_and_report(metric_name, metric_value)

        final_report = audit_hub.generate_final_report()

        self.assertTrue(os.path.exists(self.log_path))

        logger = AnomalyLogger(log_path=self.log_path)
        logs = logger.get_anomalies()

        found_in_logs = any(unique_id in str(log) for log in logs)
        self.assertTrue(found_in_logs, "Случайный ID извлеченной разметки должен присутствовать в логах аудита")

if __name__ == "__main__":
    unittest.main()