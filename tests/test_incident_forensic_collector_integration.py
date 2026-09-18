import unittest
import uuid
import random
import os
import tempfile

from skills.incident_forensic_collector import incident_forensic_collector
from skills.incident_aggregator import incident_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector


class TestIncidentForensicCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.telemetry_source = f"source-{random.randint(1000, 9999)}"
        self.error_code = random.choice([500, 502, 503, 504, 404])

    def tearDown(self):
        self.test_dir.cleanup()

    def test_collect_incident_forensic_telemetry_flow(self):
        # 1. Генерируем сырые данные через реальный системный коллектор телеметрии
        raw_telemetry = system_health_telemetry_collector(
            source=self.telemetry_source,
            metric_code=self.error_code
        )
        
        self.assertIsNotNone(raw_telemetry)

        # 2. Агрегируем инцидент без моков
        incident_package = incident_aggregator(
            incident_id=self.incident_id,
            telemetry_payload=raw_telemetry
        )

        self.assertIn("incident_id", incident_package)
        self.assertEqual(incident_package["incident_id"], self.incident_id)

        # 3. Вызываем целевой модуль автономной форензики для сбора и фиксации улик
        forensic_result = incident_forensic_collector(
            incident_data=incident_package,
            storage_path=self.test_dir.name
        )

        # Проверяем реальный возврат уникальных данных и создание артефактов
        self.assertIsInstance(forensic_result, dict)
        self.assertIn("forensic_id", forensic_result)
        
        expected_file_name = f"{self.incident_id}_forensic.log"
        expected_file_path = os.path.join(self.test_dir.name, expected_file_name)

        self.assertTrue(
            os.path.exists(expected_file_path),
            f"Форензик-лог не был записан на диск: {expected_file_path}"
        )

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(str(self.incident_id), file_content)
            self.assertIn(str(self.error_code), file_content)


if __name__ == "__main__":
    unittest.main()