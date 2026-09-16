import unittest
from unittest.mock import patch
import json
import os
import tempfile
import uuid
import random
import io
from skills.incident_sla_audit_report_exporter import incident_sla_audit_report_exporter

class TestIncidentSlaAuditReportExporter(unittest.TestCase):

    def test_export_config_mode(self):
        rand_report_id = str(uuid.uuid4())
        rand_incident_id = str(uuid.uuid4())
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        export_config = {
            "report_id": rand_report_id,
            "sla_data": {
                "incident_id": rand_incident_id,
                rand_key: rand_val
            }
        }

        res = incident_sla_audit_report_exporter(export_config=export_config)

        self.assertIsInstance(res, dict)
        self.assertIn("report_path", res)
        self.assertEqual(res["target_incident_id"], rand_incident_id)

        report_path = res["report_path"]
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["report_id"], rand_report_id)
        self.assertEqual(data["target_incident_id"], rand_incident_id)
        self.assertEqual(data["sla_data"][rand_key], rand_val)

        os.remove(report_path)

    def test_strict_mode_exception(self):
        rand_namespace = uuid.uuid4().hex

        with patch("skills.incident_sla_audit_report_exporter.module_incident_aggregator") as mock_aggregator:
            mock_aggregator.aggregate.side_effect = Exception(uuid.uuid4().hex)
            with self.assertRaises(RuntimeError):
                incident_sla_audit_report_exporter(namespace=rand_namespace, strict_mode=True)

    def test_stream_mode(self):
        rand_token = uuid.uuid4().hex

        with patch("skills.incident_sla_audit_report_exporter.extractor_tool_1789544538") as mock_extractor:
            res_str = incident_sla_audit_report_exporter(stream_mode=True, token=rand_token)
            mock_extractor.extract_audit_stream.assert_called_once()

            data = json.loads(res_str)
            self.assertEqual(data["status"], "stream_processed")
            self.assertEqual(data["token"], rand_token)

    def test_deep_audit_mode(self):
        rand_target_id = str(uuid.uuid4())
        rand_risk = round(random.uniform(0.1, 0.9), 2)
        rand_plan_id = uuid.uuid4().hex

        with patch("skills.incident_sla_audit_report_exporter.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_audit_report_exporter.incident_sla_mitigation_planner") as mock_planner:

            mock_predictor.evaluate_risk.return_value = {"risk_factor": rand_risk}
            mock_planner.generate_plan.return_value = {"mitigation_plan_id": rand_plan_id}

            res = incident_sla_audit_report_exporter(deep_audit=True, target_id=rand_target_id)

            mock_predictor.evaluate_risk.assert_called_once_with(rand_target_id)
            mock_planner.generate_plan.assert_called_once_with(rand_target_id)

            self.assertIsInstance(res, dict)
            self.assertEqual(res["risk_factor"], rand_risk)
            self.assertEqual(res["mitigation_plan_id"], rand_plan_id)

    def test_standard_export_mode(self):
        rand_sla_id = str(uuid.uuid4())
        rand_namespace = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(10, 500)

        with patch("skills.incident_sla_audit_report_exporter.module_incident_sla_tracker") as mock_tracker:
            mock_tracker.get_audit_metrics.return_value = {rand_metric_key: rand_metric_val}

            res_str = incident_sla_audit_report_exporter(sla_id=rand_sla_id, namespace=rand_namespace)
            data = json.loads(res_str)

            self.assertEqual(data["sla_id"], rand_sla_id)
            self.assertEqual(data["namespace"], rand_namespace)
            self.assertEqual(data[rand_metric_key], rand_metric_val)
            self.assertIn("compliance_score", data)
            self.assertIn("breach_count", data)