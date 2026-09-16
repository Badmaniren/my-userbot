import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine, auto_escalate_incident

class TestIncidentAutoEscalationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.incident_id = uuid.uuid4().hex
        self.workspace_dir = os.path.join("/tmp", uuid.uuid4().hex)
        os.makedirs(self.workspace_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            for f in os.listdir(self.workspace_dir):
                file_path = os.path.join(self.workspace_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.workspace_dir)

    def test_process_escalation_skipped(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_evaluator:
            
            rand_incident = {"id": self.incident_id, "data": uuid.uuid4().hex}
            mock_aggregator.get_incident.return_value = rand_incident
            mock_evaluator.evaluate.return_value = 0

            result = self.engine.process_escalation(self.incident_id)

            self.assertTrue(result.get("skipped"))
            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("severity"), 0)

    def test_process_escalation_active(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator, \
             patch("skills.incident_auto_escalation_engine.incident_severity_evaluator") as mock_evaluator, \
             patch("skills.incident_auto_escalation_engine.notification_channel_dispatcher") as mock_dispatcher, \
             patch("skills.incident_auto_escalation_engine.incident_notification_broadcaster") as mock_broadcaster:
            
            rand_incident = {"id": self.incident_id, "details": uuid.uuid4().hex}
            rand_severity = random.randint(1, 100)
            rand_channel = uuid.uuid4().hex
            
            mock_aggregator.get_incident.return_value = rand_incident
            mock_evaluator.evaluate.return_value = rand_severity
            mock_dispatcher.dispatch.return_value = rand_channel
            mock_broadcaster.broadcast.return_value = True

            result = self.engine.process_escalation(self.incident_id)

            self.assertFalse(result.get("skipped", False))
            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("severity"), rand_severity)
            self.assertEqual(result.get("escalated_to"), rand_channel)
            self.assertEqual(result.get("channel"), rand_channel)
            self.assertTrue(result.get("broadcast_success"))

    def test_evaluate_system_telemetry_risks(self):
        with patch("skills.incident_auto_escalation_engine.system_health_telemetry_collector") as mock_collector, \
             patch("skills.incident_auto_escalation_engine.incident_trend_analyzer") as mock_analyzer:
            
            metric_key = uuid.uuid4().hex
            metric_val = random.randint(10, 1000)
            telemetry_payload = {metric_key: metric_val}
            
            expected_report = {"trend": uuid.uuid4().hex, "status": uuid.uuid4().hex}

            mock_collector.collect.return_value = telemetry_payload
            mock_analyzer.analyze.return_value = expected_report

            report = self.engine.evaluate_system_telemetry_risks()

            self.assertEqual(report.get("risk_metric"), metric_val)
            self.assertEqual(report.get("trend"), expected_report["trend"])

    def test_check_and_trigger_patching_true(self):
        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner, \
             patch("skills.incident_auto_escalation_engine.auto_patch_pipeline") as mock_pipeline:
            
            vuln_list = [uuid.uuid4().hex, uuid.uuid4().hex]
            mock_scanner.scan.return_value = vuln_list
            mock_pipeline.auto_patch_pipeline.return_value = True

            res = self.engine.check_and_trigger_patching()
            self.assertTrue(res)
            mock_pipeline.auto_patch_pipeline.assert_called_once_with(vuln_list)

    def test_check_and_trigger_patching_false(self):
        with patch("skills.incident_auto_escalation_engine.vulnerability_scanner") as mock_scanner, \
             patch("skills.incident_auto_escalation_engine.auto_patch_pipeline") as mock_pipeline:
            
            mock_scanner.scan.return_value = []

            res = self.engine.check_and_trigger_patching()
            self.assertFalse(res)
            mock_pipeline.auto_patch_pipeline.assert_not_called()

    def test_consume_stream_data(self):
        with patch("skills.incident_auto_escalation_engine.incident_aggregator") as mock_aggregator:
            rand_bytes = uuid.uuid4().hex.encode('utf-8')
            mock_stream = io.BytesIO(rand_bytes)
            mock_aggregator.stream_raw_data.return_value = mock_stream

            data = self.engine.consume_stream_data()
            self.assertEqual(data, rand_bytes)

    def test_auto_escalate_incident_standalone(self):
        severity = random.randint(1, 10)
        res = auto_escalate_incident(self.incident_id, severity, self.workspace_dir)

        self.assertEqual(res.get("escalated_incident_id"), self.incident_id)
        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("severity"), severity)

        expected_file = os.path.join(self.workspace_dir, f"escalated_{self.incident_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("escalated_incident_id"), self.incident_id)
            self.assertEqual(data.get("severity"), severity)

if __name__ == "__main__":
    unittest.main()