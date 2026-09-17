import unittest
from unittest.mock import patch
import uuid
import random
import io
import datetime

from skills.incident_sla_audit_reporter import IncidentSlaAuditReporter, incident_sla_audit_reporter


class TestIncidentSlaAuditReporter(unittest.TestCase):

    def test_generate_audit_report_met(self):
        incident_id = uuid.uuid4().hex
        client_name = f"client-{uuid.uuid4().hex[:6]}"
        target = random.randint(2, 10)
        actual = random.randint(1, target)

        mock_metrics = {
            "client": client_name,
            "target_hours": target,
            "actual_hours": actual,
            "status": "MET"
        }

        with patch("skills.incident_sla_audit_reporter.IncidentSlaTracker") as mock_tracker_cls:
            instance = mock_tracker_cls.return_value
            instance.get_incident_sla_metrics.return_value = mock_metrics

            reporter = IncidentSlaAuditReporter()
            report = reporter.generate_audit_report(incident_id)

            self.assertEqual(report["incident_id"], incident_id)
            self.assertEqual(report["client"], client_name)
            self.assertEqual(report["target_hours"], target)
            self.assertEqual(report["actual_hours"], actual)
            self.assertEqual(report["status"], "MET")
            self.assertTrue(report["compliant"])
            self.assertEqual(report["compliance_score"], 100.0)
            self.assertEqual(report["deviation_factor"], round(abs(actual - target) / target, 2))
            self.assertIn("audit_id", report)
            self.assertIn("evaluated_by", report)

    def test_generate_audit_report_breached(self):
        incident_id = uuid.uuid4().hex
        client_name = f"client-{uuid.uuid4().hex[:6]}"
        target = random.randint(1, 5)
        actual = target + random.randint(1, 10)

        mock_metrics = {
            "client": client_name,
            "target_hours": target,
            "actual_hours": actual,
            "status": "BREACHED"
        }

        with patch("skills.incident_sla_audit_reporter.IncidentSlaTracker") as mock_tracker_cls:
            instance = mock_tracker_cls.return_value
            instance.get_incident_sla_metrics.return_value = mock_metrics

            reporter = IncidentSlaAuditReporter()
            report = reporter.generate_audit_report(incident_id)

            self.assertEqual(report["incident_id"], incident_id)
            self.assertEqual(report["status"], "BREACHED")
            self.assertFalse(report["compliant"])
            expected_score = max(0.0, 100.0 - (actual - target) * 10)
            self.assertEqual(report["compliance_score"], round(expected_score, 2))
            self.assertGreater(report["deviation_factor"], 0.0)

    def test_export_report_stream(self):
        incident_id = uuid.uuid4().hex
        mock_metrics = {
            "client": f"client-{uuid.uuid4().hex[:6]}",
            "target_hours": 4,
            "actual_hours": 2,
            "status": "MET"
        }

        stream = io.BytesIO()

        with patch("skills.incident_sla_audit_reporter.IncidentSlaTracker") as mock_tracker_cls:
            instance = mock_tracker_cls.return_value
            instance.get_incident_sla_metrics.return_value = mock_metrics

            reporter = IncidentSlaAuditReporter()
            result = reporter.export_report_stream(incident_id, stream)

            self.assertTrue(result)
            stream.seek(0)
            data = stream.read()
            self.assertIsInstance(data, bytes)
            self.assertTrue(len(data) > 0)

    def test_batch_audit_compliance(self):
        incident_ids = [uuid.uuid4().hex for _ in range(3)]

        mock_metrics_list = [
            {"client": "A", "target_hours": 2, "actual_hours": 1, "status": "MET"},
            {"client": "B", "target_hours": 2, "actual_hours": 5, "status": "BREACHED"},
            {"client": "C", "target_hours": 3, "actual_hours": 3, "status": "MET"}
        ]

        with patch("skills.incident_sla_audit_reporter.IncidentSlaTracker") as mock_tracker_cls:
            instance = mock_tracker_cls.return_value
            instance.get_incident_sla_metrics.side_effect = mock_metrics_list

            reporter = IncidentSlaAuditReporter()
            batch_result = reporter.batch_audit_compliance(incident_ids)

            self.assertEqual(batch_result["total_evaluated"], 3)
            self.assertEqual(batch_result["compliance_rate"], 66.67)
            self.assertEqual(len(batch_result["details"]), 3)

    def test_functional_wrapper(self):
        incident_id = uuid.uuid4().hex
        payload = {"incident_id": incident_id}
        mock_metrics = {
            "client": f"client-{uuid.uuid4().hex[:6]}",
            "target_hours": 5,
            "actual_hours": 3,
            "status": "MET"
        }

        with patch("skills.incident_sla_audit_reporter.IncidentSlaTracker") as mock_tracker_cls:
            instance = mock_tracker_cls.return_value
            instance.get_incident_sla_metrics.return_value = mock_metrics

            result = incident_sla_audit_reporter(payload)

            self.assertEqual(result["incident_id"], incident_id)
            self.assertIn("audit_timestamp", result)
            self.assertTrue(result["sla_compliant"])


if __name__ == "__main__":
    unittest.main()