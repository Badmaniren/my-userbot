import unittest
import uuid
import random
import os
import tempfile
from skills.extractor_tool_1793211982 import ExtractorTool
from skills.anomaly_logger import AnomalyLogger

class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"anomaly_{uuid.uuid4()}.log")
        self.extractor = ExtractorTool()
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extractor_integration_with_logger(self):
        unique_id = str(uuid.uuid4())
        random_severity = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        markup_sample = f'<metadata id="{unique_id}" severity="{random_severity}" description="integration test markup" />'

        extracted_data = self.extractor.extract(markup_sample)

        self.assertIn(unique_id, str(extracted_data))

        self.logger.log_anomaly(
            source="extractor_tool_1793211982",
            severity=random_severity,
            details=extracted_data,
            telemetry_snapshot={"test_id": unique_id}
        )

        self.assertTrue(os.path.exists(self.log_path), "Лог-файл должен быть создан в процессе интеграции")

        anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1, "Лог должен содержать записанную аномалию")

        latest_anomaly = anomalies[-1]
        self.assertEqual(latest_anomaly.get("source"), "extractor_tool_1793211982")
        self.assertEqual(latest_anomaly.get("severity"), random_severity)

if __name__ == "__main__":
    unittest.main()
