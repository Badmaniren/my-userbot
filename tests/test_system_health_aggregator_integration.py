import unittest
import os
import uuid
import random
from skills.system_health_aggregator import SystemHealthAggregator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.test_file_path = f"test_health_report_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            try:
                os.remove(self.test_file_path)
            except OSError:
                pass

    def test_process_and_broadcast_health_integration(self):
        rand_id = f"INC-{random.randint(1000, 9999)}"
        rand_msg = f"System unstable due to error code {uuid.uuid4()}"
        module_name = f"module_{uuid.uuid4().hex[:6]}"
        channel_name = f"channel_{uuid.uuid4().hex[:6]}"

        incident_data = {
            "incident_id": rand_id,
            "message": rand_msg,
            "severity": "CRITICAL"
        }

        audit_summary = {"status": "failed", "vulnerabilities": random.randint(0, 5)}
        metrics = {"cpu_usage": random.uniform(80.0, 99.9), "memory_usage": random.uniform(70.0, 95.0)}

        # Регистрация канала в диспетчере через агрегатор для прохождения реальной отправки
        if hasattr(self.aggregator.dispatcher, "register_channel"):
            self.aggregator.dispatcher.register_channel(channel_name, {"type": "mock", "active": True})

        result = self.aggregator.process_and_broadcast_health(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            channel_name=channel_name,
            report_file_path=self.test_file_path
        )

        self.assertIn("report", result)
        self.assertIn("dispatch_success", result)
        self.assertTrue(result["dispatch_success"])

        # Проверка генерации отчета и его экспорта (реальный файл)
        report = result["report"]
        self.assertIsNotNone(report)
        self.assertTrue(os.path.exists(self.test_file_path), "Файл отчета должен быть создан на диске")

        with open(self.test_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(module_name, file_content)

    def test_process_stream_health_data_integration(self):
        channel_name = f"stream_channel_{uuid.uuid4().hex[:6]}"
        rand_id = f"STREAM-INC-{random.randint(100, 999)}"
        rand_msg = f"Stream alert message {uuid.uuid4()}"

        stream_data = f'{{"level": "WARNING", "incident_id": "{rand_id}", "message": "{rand_msg}"}}'

        if hasattr(self.aggregator.dispatcher, "register_channel"):
            self.aggregator.dispatcher.register_channel(channel_name, {"type": "stream", "active": True})

        success = self.aggregator.process_stream_health_data(stream_data, channel_name)
        self.assertTrue(success, "Потоковая обработка и диспетчеризация должны завершиться успешно")

if __name__ == "__main__":
    unittest.main()