import unittest
from unittest.mock import patch, MagicMock
import os
import json
import io
import uuid
import random
import string

from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    auto_escalate_incident
)

class TestIncidentAutoEscalationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.random_incident_id = uuid.uuid4().hex
        self.random_severity = random.randint(1, 10)
        self.random_workspace = f"/tmp/{uuid.uuid4().hex}"

    def test_process_escalation_high_severity(self):
        mock_incident = {"id": self.random_incident_id, "type": "breach"}
        mock_channel = f"channel_{uuid.uuid4().hex[:6]}"
        
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_agg, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_sev, \
             patch("skills.incident_auto_escalation_engine.notification_channel_dispatcher") as mock_disp, \
             patch("skills.incident_auto_escalation_engine.incident_notification_broadcaster") as mock_broad:
            
            mock_agg.get_incident.return_value = mock_incident
            mock_sev.evaluate.return_value = self.random_severity
            mock_disp.dispatch.return_value = mock_channel
            mock_broad.broadcast.return_value = True

            result = self.engine.process_escalation(self.random_incident_id)

            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["severity"], self.random_severity)
            self.assertEqual(result["escalated_to"], mock_channel)
            self.assertTrue(result["broadcast_success"])
            mock_agg.get_incident.assert_called_once_with(self.random_incident_id)

    def test_process_escalation_low_severity_skip(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_agg, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_sev:
            
            mock_agg.get_incident.return_value = {"id": self.random_incident_id}
            mock_sev.evaluate.return_value = 0

            result = self.engine.process_escalation(self.random_incident_id)

            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["severity"], 0)
            self.assertTrue(result["skipped"])

    def test_evaluate_system_telemetry_risks(self):
        random_key = uuid.uuid4().hex
        random_val = random.randint(50, 500)
        telemetry_mock = {random_key: random_val}
        trend_mock = {"trend": "".join(random.choices(string.ascii_lowercase, k=6))}

        with patch("skills.incident_auto_escalation_engine.system_health_telemetry_collector") as mock_telemetry, \
             patch("skills.incident_auto_escalation_engine.incident_trend_analyzer") as mock_trend:
            
            mock_telemetry.collect.return_value = telemetry_mock
            mock_trend.analyze.return_value = trend_mock

            report = self.engine.evaluate_system_telemetry_risks()

            self.assertEqual(report["risk_metric"], random_val)
            self.assertEqual(report["trend"], trend_mock["trend"])
            mock_trend.analyze.assert_called_once_with(telemetry_mock)

    def test_check_and_trigger_patching_with_vulnerabilities(self):
        vuln_list = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner, \
             patch("skills.incident_auto_escalation_engine.auto_patch_pipeline") as mock_pipeline:
            
            mock_scanner.scan.return_value = vuln_list
            mock_pipeline.auto_patch_pipeline.return_value = True

            triggered = self.engine.check_and_trigger_patching()

            self.assertTrue(triggered)
            mock_pipeline.auto_patch_pipeline.assert_called_once_with(vuln_list)

    def test_check_and_trigger_patching_empty(self):
        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner:
            mock_scanner.scan.return_value = []

            triggered = self.engine.check_and_trigger_patching()

            self.assertFalse(triggered)

    def test_consume_stream_data(self):
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_agg:
            mock_agg.stream_raw_data.return_value = mock_stream

            data = self.engine.consume_stream_data()

            self.assertEqual(data, random_bytes)

    def test_auto_escalate_incident_function(self):
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            
            res = auto_escalate_incident(self.random_incident_id, self.random_severity, self.random_workspace)

            self.assertEqual(res["escalated_incident_id"], self.random_incident_id)
            self.assertEqual(res["severity"], self.random_severity)
            self.assertEqual(res["status"], "SUCCESS")
            mock_makedirs.assert_called_once_with(self.random_workspace, exist_ok=True)
            mock_file.assert_called_once()

if __name__ == "__main__":
    unittest.main()