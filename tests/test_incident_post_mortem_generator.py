import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string

from skills.incident_post_mortem_generator import (
    IncidentPostMortemGenerator,
    PostMortemReport,
    PostMortemGenerationError,
    IncidentNotFoundError,
    IncompleteRecoveryDataError,
    generate_incident_post_mortem,
)


class TestIncidentPostMortemGenerator(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex
        self.service_name = "".join(random.choices(string.ascii_lowercase, k=8))
        self.severity = random.choice(["SEV1", "SEV2", "SEV3"])
        self.root_cause = "".join(random.choices(string.ascii_letters, k=15))
        self.component = "".join(random.choices(string.ascii_lowercase, k=6))
        self.audit_url = f"http://{uuid.uuid4().hex}.local/audit"

        self.mock_aggregator = MagicMock()
        self.mock_recovery_hub = MagicMock()
        self.mock_exporter = MagicMock()
        self.mock_broadcaster = MagicMock()

        self.generator = IncidentPostMortemGenerator(
            incident_aggregator=self.mock_aggregator,
            error_recovery_hub=self.mock_recovery_hub,
            recovery_report_exporter=self.mock_exporter,
            notification_broadcaster=self.mock_broadcaster,
        )

    def test_generate_post_mortem_success(self):
        incident_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
            "severity": self.severity,
            "root_cause_summary": self.root_cause,
            "affected_components": [self.component],
            "detected_at": 100.0,
            "resolved_at": 400.0,
            "occurred_at": 50.0,
            "external_audit_url": self.audit_url,
        }
        self.mock_aggregator.get_incident.return_value = incident_data

        recovery_logs = [
            {
                "timestamp": 150.0,
                "action": "restart_service",
                "details": "Restarted container successfully",
            }
        ]
        self.mock_recovery_hub.get_recovery_logs.return_value = recovery_logs

        remote_payload = {"audit_status": "passed", "token": uuid.uuid4().hex}
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = remote_payload
            mock_get.return_value = mock_resp

            report = self.generator.generate_post_mortem(
                self.incident_id, allow_partial=False, fetch_remote_audit=True
            )

        self.assertIsInstance(report, PostMortemReport)
        self.assertEqual(report.incident_id, self.incident_id)
        self.assertEqual(report.service, self.service_name)
        self.assertEqual(report.severity, self.severity)
        self.assertEqual(report.root_cause, self.root_cause)
        self.assertEqual(report["remote_audit"], remote_payload)
        self.assertFalse(report["is_partial"])

        self.assertEqual(report.metrics["mttd_seconds"], 50.0)
        self.assertEqual(report.metrics["mttr_seconds"], 300.0)

        self.assertEqual(len(report.timeline), 3)
        self.assertEqual(report.timeline[0]["event"], "Incident Occurred")
        self.assertEqual(report.timeline[1]["event"], "restart_service")
        self.assertEqual(report.timeline[2]["event"], "Incident Resolved")

        self.assertIn(f"Investigate and patch component {self.component}", report.action_items)

    def test_incident_not_found(self):
        self.mock_aggregator.get_incident.return_value = None

        with self.assertRaises(IncidentNotFoundError):
            self.generator.generate_post_mortem(self.incident_id)

    def test_incomplete_recovery_data_error(self):
        incident_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
        }
        self.mock_aggregator.get_incident.return_value = incident_data
        self.mock_recovery_hub.get_recovery_logs.return_value = []

        with self.assertRaises(IncompleteRecoveryDataError):
            self.generator.generate_post_mortem(self.incident_id, allow_partial=False)

        report = self.generator.generate_post_mortem(self.incident_id, allow_partial=True)
        self.assertTrue(report["is_partial"])

    def test_export_report_markdown_string_stream(self):
        report_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "remote_audit": {"info": uuid.uuid4().hex},
        }
        report = PostMortemReport(report_data)
        stream = io.StringIO()

        self.generator.export_report(report, stream, format_type="markdown")
        content = stream.getvalue()

        self.assertIn(self.incident_id, content)
        self.assertIn(self.service_name, content)
        self.assertIn(self.severity, content)
        self.assertIn(self.root_cause, content)

    def test_export_report_markdown_bytes_stream(self):
        report_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "remote_audit": {},
        }
        stream = io.BytesIO()

        self.generator.export_report(report_data, stream, format_type="markdown")
        content = stream.getvalue().decode("utf-8")

        self.assertIn(self.incident_id, content)

    def test_export_report_json(self):
        report_data = {
            "incident_id": self.incident_id,
            "service": self.service_name,
        }
        stream = io.StringIO()

        self.generator.export_report(report_data, stream, format_type="json")
        content = stream.getvalue()
        parsed = json.loads(content)

        self.assertEqual(parsed["data"]["incident_id"], self.incident_id)

    def test_publish_post_mortem(self):
        destinations = [uuid.uuid4().hex, uuid.uuid4().hex]
        report_data = {"incident_id": self.incident_id}
        report = PostMortemReport(report_data)

        res = self.generator.publish_post_mortem(report, destinations)
        self.assertTrue(res)
        self.mock_broadcaster.broadcast.assert_called_once_with(report_data, destinations=destinations)

    def test_legacy_generate_incident_post_mortem(self):
        error_code = uuid.uuid4().hex
        incident_details = {
            "detected_at": 200.0,
            "occurred_at": 100.0,
            "resolved_at": 500.0,
            "error_code": error_code,
            "service": self.service_name,
            "root_cause_summary": self.root_cause,
        }
        recovery_data = [{"action": "reboot"}]

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            filename = generate_incident_post_mortem(self.incident_id, incident_details, recovery_data)
            self.assertEqual(filename, f"post_mortem_{self.incident_id}.md")
            mock_file.assert_called_once_with(filename, "w", encoding="utf-8")
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn(self.incident_id, written_content)
            self.assertIn(error_code, written_content)
            self.assertIn(self.service_name, written_content)