import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.incident_forensics_audit_archiver import (
    archive_incident_forensics_data,
    IncidentForensicsAuditArchiver
)
from skills.incident_audit_trail_collector import collect_incident_audit_trail
from skills.recovery_report_exporter import RecoveryReportExporter


class TestIncidentForensicsAuditArchiverIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.epic_id = f"epic-{uuid.uuid4()}"
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.destination_path = os.path.join(self.test_dir, f"audit_trail_{uuid.uuid4()}.json")
        self.export_path = os.path.join(self.test_dir, f"forensics_report_{uuid.uuid4()}.json")

        self.incident_data = {
            "incident_id": self.incident_id,
            "error_code": random.choice(["ERR_AUTH_FAIL", "ERR_DB_TIMEOUT", "ERR_MEM_LEAK"]),
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "random_metric": random.random()
        }

        self.summary_payload = {
            "status": "ARCHIVED",
            "random_score": random.randint(1, 100)
        }

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_end_to_end_forensics_archival(self):
        # Проверяем композицию: запуск функции архивации должна вызывать сбор аудита
        # и экспортер отчетов без использования моков между реальными навыками.

        result = archive_incident_forensics_data(
            incident_data=self.incident_data,
            destination_path=self.destination_path,
            include_raw_telemetry=True,
            module_name=self.module_name,
            exception=RuntimeError("Random integration failure"),
            traceback_str="Traceback (most recent call last): file.py",
            incident_id=self.incident_id,
            epic_id=self.epic_id,
            stream="forensics-stream",
            summary_payload=self.summary_payload,
            export_format="json",
            output_path=self.export_path
        )

        self.assertIsNotNone(result)

        # Проверяем реальное появление файлов на диске, созданных через реальные зависимости
        self.assertTrue(
            os.path.exists(self.destination_path),
            "Аудит трейл не был сохранен реальным коллектором."
        )

        self.assertTrue(
            os.path.exists(self.export_path),
            "Отчет форензика не был экспортирован реальным репортером."
        )

        with open(self.destination_path, "r", encoding="utf-8") as f:
            content_audit = f.read()
            self.assertIn(self.incident_id, content_audit)

        with open(self.export_path, "r", encoding="utf-8") as f:
            content_report = f.read()
            self.assertIn(self.epic_id, content_report)

    def test_class_based_archiver_workflow(self):
        archiver = IncidentForensicsAuditArchiver()

        audit_res = archiver.collect_and_export_trail(
            incident_data=self.incident_data,
            destination_path=self.destination_path,
            include_raw_telemetry=False
        )
        self.assertIsNotNone(audit_res)
        self.assertTrue(os.path.exists(self.destination_path))

        report_res = archiver.export_report(
            module_name=self.module_name,
            exception=ValueError("Random validation error"),
            traceback_str="Traceback...",
            incident_id=self.incident_id,
            audit_data=self.incident_data,
            epic_id=self.epic_id,
            stream="audit-stream",
            summary_payload=self.summary_payload,
            export_format="json",
            output_path=self.export_path
        )
        self.assertIsNotNone(report_res)
        self.assertTrue(os.path.exists(self.export_path))


if __name__ == "__main__":
    unittest.main()