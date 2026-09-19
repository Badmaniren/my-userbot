import unittest
from unittest.mock import patch
import io
import os
import json
import uuid
import random
from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    auto_escalate_incident
)

class TestIncidentAutoEscalationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.incident_id = uuid.uuid4().hex
        self.workspace_dir = f"temp_workspace_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            for root, dirs, files in os.walk(self.workspace_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.workspace_dir)

    def test_process_escalation_skipped(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_evaluator:
            
            mock_incident = {"id": self.incident_id, "data": uuid.uuid4().hex}
            mock_aggregator.get_incident.return_value = mock_incident
            
            negative_severity = -random.randint(1, 100)
            mock_evaluator.evaluate.return_value = negative_severity

            result = self.engine.process_escalation(self.incident_id)

            mock_aggregator.get_incident.assert_called_once_with(self.incident_id)
            mock_evaluator.evaluate.assert_called_once_with(mock_incident)
            
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["severity"], negative_severity)
            self.assertTrue(result["skipped"])

    def test_process_escalation_success(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_evaluator, \
             patch("skills.incident_auto_escalation_engine.notification_channel_dispatcher") as mock_dispatcher, \
             patch("skills.incident_auto_escalation_engine.incident_notification_broadcaster") as mock_broadcaster:
            
            mock_incident = {"id": self.incident_id, "type": uuid.uuid4().hex}
            mock_aggregator.get_incident.return_value = mock_incident
            
            positive_severity = random.randint(1, 10)
            mock_evaluator.evaluate.return_value = positive_severity
            
            expected_channel = f"channel_{uuid.uuid4().hex[:6]}"
            mock_dispatcher.dispatch.return_value = expected_channel
            
            mock_broadcaster.broadcast.return_value = True

            result = self.engine.process_escalation(self.incident_id)

            mock_aggregator.get_incident.assert_called_once_with(self.incident_id)
            mock_evaluator.evaluate.assert_called_once_with(mock_incident)
            mock_dispatcher.dispatch.assert_called_once_with(mock_incident)
            mock_broadcaster.broadcast.assert_called_once_with(mock_incident)

            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["severity"], positive_severity)
            self.assertEqual(result["escalated_to"], expected_channel)
            self.assertEqual(result["channel"], expected_channel)
            self.assertTrue(result["broadcast_success"])

    def test_evaluate_system_telemetry_risks(self):
        with patch("skills.incident_auto_escalation_engine.system_health_telemetry_collector") as mock_collector, \
             patch("skills.incident_auto_escalation_engine.incident_trend_analyzer") as mock_analyzer:
            
            metric_key = uuid.uuid4().hex
            metric_val = random.randint(50, 1000)
            telemetry_mock_data = {metric_key: metric_val}
            mock_collector.collect.return_value = telemetry_mock_data

            expected_trend = {"trend": uuid.uuid4().hex, "status": uuid.uuid4().hex}
            mock_analyzer.analyze.return_value = expected_trend

            result = self.engine.evaluate_system_telemetry_risks()

            mock_collector.collect.assert_called_once()
            mock_analyzer.analyze.assert_called_once_with(telemetry_mock_data)

            self.assertEqual(result["risk_metric"], metric_val)
            self.assertEqual(result["trend"], expected_trend["trend"])
            self.assertEqual(result["status"], expected_trend["status"])

    def test_check_and_trigger_patching_true(self):
        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner, \
             patch("skills.incident_auto_escalation_engine.auto_patch_pipeline") as mock_pipeline:
            
            vulnerabilities = [uuid.uuid4().hex, uuid.uuid4().hex]
            mock_scanner.scan.return_value = vulnerabilities
            mock_pipeline.auto_patch_pipeline.return_value = True

            result = self.engine.check_and_trigger_patching()

            mock_scanner.scan.assert_called_once()
            mock_pipeline.auto_patch_pipeline.assert_called_once_with(vulnerabilities)
            self.assertTrue(result)

    def test_check_and_trigger_patching_false(self):
        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner:
            mock_scanner.scan.return_value = []

            result = self.engine.check_and_trigger_patching()

            mock_scanner.scan.assert_called_once()
            self.assertFalse(result)

    def test_consume_stream_data(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator:
            random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
            mock_stream = io.BytesIO(random_bytes)
            mock_aggregator.stream_raw_data.return_value = mock_stream

            result = self.engine.consume_stream_data()

            mock_aggregator.stream_raw_data.assert_called_once()
            self.assertEqual(result, random_bytes)

    def test_auto_escalate_incident_file_creation(self):
        severity = random.randint(1, 5)
        result = auto_escalate_incident(self.incident_id, severity, self.workspace_dir)

        self.assertEqual(result["escalated_incident_id"], self.incident_id)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["severity"], severity)

        expected_file_path = os.path.join(self.workspace_dir, f"escalated_{self.incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["escalated_incident_id"], self.incident_id)
        self.assertEqual(file_data["severity"], severity)
        self.assertEqual(file_data["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()