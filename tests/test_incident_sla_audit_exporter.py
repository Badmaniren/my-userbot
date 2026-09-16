import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_sla_audit_exporter import IncidentSLAAuditExporter

class TestIncidentSLAAuditExporter(unittest.TestCase):

    def setUp(self):
        self.tracker_module = "skills.incident_sla_tracker"
        self.planner_module = "skills.incident_sla_mitigation_planner"

    def test_export_audit_report_success(self):
        random_incident_id = uuid.uuid4().hex
        random_status = random.choice(["COMPLIANT", "BREACHED", "WARNING"])
        random_metric = round(random.uniform(85.0, 99.9), 2)
        random_mitigation_step = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        tracker_mock_data = {
            "incident_id": random_incident_id,
            "sla_status": random_status,
            "compliance_score": random_metric
        }

        planner_mock_data = {
            "incident_id": random_incident_id,
            "mitigation_plan": random_mitigation_step,
            "priority": random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        }

        with patch(f"{self.tracker_module}.IncidentSLATracker") as mock_tracker_cls, \
             patch(f"{self.planner_module}.IncidentSLAMitigationPlanner") as mock_planner_cls:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.get_incident_sla_record.return_value = tracker_mock_data

            mock_planner_instance = mock_planner_cls.return_value
            mock_planner_instance.get_mitigation_details.return_value = planner_mock_data

            exporter = IncidentSLAAuditExporter()
            report = exporter.export_audit_report(random_incident_id)

            self.assertIn("audit_metadata", report)
            self.assertEqual(report["incident_id"], random_incident_id)
            self.assertEqual(report["sla_status"], random_status)
            self.assertEqual(report["compliance_score"], random_metric)
            self.assertEqual(report["mitigation_plan"], random_mitigation_step)

            mock_tracker_instance.get_incident_sla_record.assert_called_once_with(random_incident_id)
            mock_planner_instance.get_mitigation_details.assert_called_once_with(random_incident_id)

    def test_export_audit_report_missing_data(self):
        random_incident_id = uuid.uuid4().hex

        with patch(f"{self.tracker_module}.IncidentSLATracker") as mock_tracker_cls, \
             patch(f"{self.planner_module}.IncidentSLAMitigationPlanner") as mock_planner_cls:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.get_incident_sla_record.return_value = None

            mock_planner_instance = mock_planner_cls.return_value
            mock_planner_instance.get_mitigation_details.return_value = None

            exporter = IncidentSLAAuditExporter()
            report = exporter.export_audit_report(random_incident_id)

            self.assertIn("error", report)
            self.assertEqual(report["incident_id"], random_incident_id)
            self.assertIsNone(report.get("sla_status"))

    def test_export_bulk_audit_reports(self):
        incident_ids = [uuid.uuid4().hex for _ in range(random.randint(2, 5))]
        expected_status = random.choice(["COMPLIANT", "BREACHED"])

        with patch(f"{self.tracker_module}.IncidentSLATracker") as mock_tracker_cls, \
             patch(f"{self.planner_module}.IncidentSLAMitigationPlanner") as mock_planner_cls:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_planner_instance = mock_planner_cls.return_value

            def side_effect_tracker(inc_id):
                return {"incident_id": inc_id, "sla_status": expected_status, "compliance_score": 95.0}

            def side_effect_planner(inc_id):
                return {"incident_id": inc_id, "mitigation_plan": "action_" + inc_id[:6]}

            mock_tracker_instance.get_incident_sla_record.side_effect = side_effect_tracker
            mock_planner_instance.get_mitigation_details.side_effect = side_effect_planner

            exporter = IncidentSLAAuditExporter()
            bulk_reports = exporter.export_bulk_audit_reports(incident_ids)

            self.assertEqual(len(bulk_reports), len(incident_ids))
            for rep in bulk_reports:
                self.assertIn(rep["incident_id"], incident_ids)
                self.assertEqual(rep["sla_status"], expected_status)

    def test_export_audit_report_stream_output(self):
        random_incident_id = uuid.uuid4().hex
        random_status = "COMPLIANT"

        tracker_mock_data = {
            "incident_id": random_incident_id,
            "sla_status": random_status,
            "compliance_score": 99.9
        }
        planner_mock_data = {
            "incident_id": random_incident_id,
            "mitigation_plan": "none"
        }

        with patch(f"{self.tracker_module}.IncidentSLATracker") as mock_tracker_cls, \
             patch(f"{self.planner_module}.IncidentSLAMitigationPlanner") as mock_planner_cls:

            mock_tracker_instance = mock_tracker_cls.return_value
            mock_tracker_instance.get_incident_sla_record.return_value = tracker_mock_data

            mock_planner_instance = mock_planner_cls.return_value
            mock_planner_instance.get_mitigation_details.return_value = planner_mock_data

            exporter = IncidentSLAAuditExporter()
            stream = io.BytesIO()
            exporter.export_audit_report_to_stream(random_incident_id, stream)

            stream.seek(0)
            data = json.loads(stream.read().decode('utf-8'))
            self.assertEqual(data["incident_id"], random_incident_id)
            self.assertEqual(data["sla_status"], random_status)

if __name__ == '__main__':
    unittest.main()