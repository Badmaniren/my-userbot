import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.audit_export_bridge import AuditExportBridge

class TestAuditExportBridge(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.9)
        self.output_path = f"/exports/{uuid.uuid4().hex}.json"
        self.metric_name = ''.join(random.choices(string.ascii_letters, k=10))
        self.metric_value = random.randint(1, 1000)

    def test_bridge_transfer_integrity(self):
        """
        Проверка целостности передачи данных:
        Bridge должен извлечь отчет из AnomalyAuditHub и передать его в DigestExporter.
        """
        mock_report = {"id": uuid.uuid4().hex, "data": random.random()}

        with patch('skills.audit_export_bridge.AnomalyAuditHub') as MockHub, \
             patch('skills.audit_export_bridge.DigestExporter') as MockExporter:

            instance_hub = MockHub.return_value
            instance_hub.generate_final_report.return_value = mock_report

            instance_exporter = MockExporter.return_value
            instance_exporter.export_json_report.return_value = self.output_path

            bridge = AuditExportBridge(self.repo_path, self.log_path, self.threshold)
            result = bridge.transfer_report(self.output_path)

            instance_hub.generate_final_report.assert_called_once()
            instance_exporter.export_json_report.assert_called_with(self.output_path)
            self.assertEqual(result, self.output_path)

    def test_bridge_aggregation_flow(self):
        """
        Проверка корректности вызова агрегации перед экспортом.
        """
        with patch('skills.audit_export_bridge.AnomalyAuditHub') as MockHub, \
             patch('skills.audit_export_bridge.DigestExporter') as MockExporter:

            bridge = AuditExportBridge(self.repo_path, self.log_path, self.threshold)
            bridge.aggregate_and_push(self.metric_name, self.metric_value, self.output_path)

            MockHub.return_value.aggregate_and_report.assert_called_with(
                self.metric_name, self.metric_value
            )
            MockExporter.return_value.export_json_report.assert_called_once()

    def test_bridge_error_handling(self):
        """
        Проверка обработки исключений при сбое экспортера.
        """
        from skills.digest_exporter import DigestExporterError

        with patch('skills.audit_export_bridge.AnomalyAuditHub'), \
             patch('skills.audit_export_bridge.DigestExporter') as MockExporter:

            instance_exporter = MockExporter.return_value
            instance_exporter.export_json_report.side_effect = DigestExporterError("Export failed")

            bridge = AuditExportBridge(self.repo_path, self.log_path, self.threshold)

            with self.assertRaises(DigestExporterError):
                bridge.transfer_report(self.output_path)

    def test_telemetry_snapshot_integrity(self):
        """
        Проверка передачи снимка телеметрии через bridge в hub.
        """
        source = uuid.uuid4().hex
        severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details = f"Anomaly detected: {uuid.uuid4().hex}"
        snapshot = {"cpu": random.random(), "mem": random.random()}

        with patch('skills.audit_export_bridge.AnomalyAuditHub') as MockHub:
            bridge = AuditExportBridge(self.repo_path, self.log_path, self.threshold)
            bridge.log_bridge_anomaly(source, severity, details, snapshot)

            MockHub.return_value.log_anomaly.assert_called_with(
                source, severity, details, snapshot
            )

if __name__ == '__main__':
    unittest.main()