import unittest
from unittest.mock import patch
import os
import json
import io
import uuid
import random
from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    auto_escalate_incident
)

class TestIncidentAutoEscalationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = IncidentAutoEscalationEngine()
        self.random_incident_id = uuid.uuid4().hex
        self.random_workspace = f"workspace_{uuid.uuid4().hex[:8]}"

    def tearDown(self) -> None:
        if os.path.exists(self.random_workspace):
            for root, dirs, files in os.walk(self.random_workspace, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.random_workspace)

    def test_process_escalation_skipped(self) -> None:
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_evaluator:
            
            mock_aggregator.get_incident.return_value = {"id": self.random_incident_id}
            mock_evaluator.evaluate.return_value = random.randint(-5, 0)

            result = self.engine.process_escalation(self.random_incident_id)

            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertTrue(result["skipped"])
            self.assertLessEqual(result["severity"], 0)

    def test_process_escalation_success(self) -> None:
        expected_severity = random.randint(1, 100)
        expected_channel = f"channel_{uuid.uuid4().hex[:6]}"
        expected_broadcast = random.choice([True, False])

        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_evaluator, \
             patch("skills.incident_auto_escalation_engine.notification_channel_dispatcher") as mock_dispatcher, \
             patch("skills.incident_auto_escalation_engine.incident_notification_broadcaster") as mock_broadcaster:
            
            mock_aggregator.get_incident.return_value = {"id": self.random_incident_id}
            mock_evaluator.evaluate.return_value = expected_severity
            mock_dispatcher.dispatch.return_value = expected_channel
            mock_broadcaster.broadcast.return_value = expected_broadcast

            result = self.engine.process_escalation(self.random_incident_id)

            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["severity"], expected_severity)
            self.assertEqual(result["escalated_to"], expected_channel)
            self.assertEqual(result["channel"], expected_channel)
            self.assertEqual(result["broadcast_success"], expected_broadcast)

    def test_evaluate_system_telemetry_risks(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        metric_value = random.randint(10, 500)
        telemetry_payload = {metric_name: metric_value}
        trend_payload = {"trend": f"trend_{uuid.uuid4().hex[:4]}"}

        with patch("skills.incident_auto_escalation_engine.system_health_telemetry_collector") as mock_collector, \
             patch("skills.incident_auto_escalation_engine.incident_trend_analyzer") as mock_analyzer:
            
            mock_collector.collect.return_value = telemetry_payload
            mock_analyzer.analyze.return_value = trend_payload

            result = self.engine.evaluate_system_telemetry_risks()

            self.assertEqual(result["risk_metric"], metric_value)
            self.assertIn("trend", result)

    def test_check_and_trigger_patching_true(self) -> None:
        vulnerabilities_list = [f"CVE-{random.randint(1000, 9999)}"]

        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner, \
             patch("skills.incident_auto_escalation_engine.auto_patch_pipeline") as mock_pipeline:
            
            mock_scanner.scan.return_value = vulnerabilities_list
            mock_pipeline.auto_patch_pipeline.return_value = True

            res = self.engine.check_and_trigger_patching()
            self.assertTrue(res)

    def test_check_and_trigger_patching_false(self) -> None:
        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner:
            mock_scanner.scan.return_value = []

            res = self.engine.check_and_trigger_patching()
            self.assertFalse(res)

    def test_consume_stream_data(self) -> None:
        random_bytes = uuid.uuid4().bytes

        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator:
            mock_stream = io.BytesIO(random_bytes)
            mock_aggregator.stream_raw_data.return_value = mock_stream

            data = self.engine.consume_stream_data()
            self.assertEqual(data, random_bytes)

    def test_auto_escalate_incident_file_creation(self) -> None:
        severity = random.randint(1, 10)
        result = auto_escalate_incident(self.random_incident_id, severity, self.random_workspace)

        self.assertEqual(result["escalated_incident_id"], self.random_incident_id)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["severity"], severity)

        expected_file_path = os.path.join(self.random_workspace, f"escalated_{self.random_incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["escalated_incident_id"], self.random_incident_id)
        self.assertEqual(file_data["status"], "SUCCESS")
        self.assertEqual(file_data["severity"], severity)