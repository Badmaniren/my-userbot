import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine

class TestIncidentAutoEscalationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()

    def test_evaluate_and_escalate_incident_success(self):
        inc_id = str(uuid.uuid4())
        sev_score = random.randint(1, 100)
        channel_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        webhook_url = f"https://{ ''.join(random.choices(string.ascii_lowercase, k=8)) }.com/webhook"

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = sev_score

        mock_aggregator = MagicMock()
        mock_aggregator.get_incident.return_value = {
            "id": inc_id,
            "payload": ''.join(random.choices(string.ascii_letters, k=25))
        }

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = channel_name

        mock_broadcaster = MagicMock()
        mock_broadcaster.broadcast.return_value = True

        with patch('skills.incident_auto_escalation_engine.incident_severity_evaluator', mock_evaluator), \
             patch('skills.incident_auto_escalation_engine.incident_aggregator', mock_aggregator), \
             patch('skills.incident_auto_escalation_engine.notification_channel_dispatcher', mock_dispatcher), \
             patch('skills.incident_auto_escalation_engine.incident_notification_broadcaster', mock_broadcaster):

            result = self.engine.process_escalation(inc_id)

            mock_aggregator.get_incident.assert_called_once_with(inc_id)
            mock_evaluator.evaluate.assert_called_once()
            mock_dispatcher.dispatch.assert_called_once()
            mock_broadcaster.broadcast.assert_called_once()
            
            self.assertIn("escalated_to", result)
            self.assertEqual(result["incident_id"], inc_id)
            self.assertEqual(result["severity"], sev_score)
            self.assertEqual(result["channel"], channel_name)

    def test_process_escalation_low_severity_ignored(self):
        inc_id = str(uuid.uuid4())
        low_sev = random.randint(-50, 0)

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = low_sev

        mock_aggregator = MagicMock()
        mock_aggregator.get_incident.return_value = {
            "id": inc_id,
            "payload": ''.join(random.choices(string.ascii_letters, k=15))
        }

        with patch('skills.incident_auto_escalation_engine.incident_severity_evaluator', mock_evaluator), \
             patch('skills.incident_auto_escalation_engine.incident_aggregator', mock_aggregator):

            result = self.engine.process_escalation(inc_id)

            self.assertTrue(result.get("skipped"))
            self.assertEqual(result["incident_id"], inc_id)
            self.assertEqual(result["severity"], low_sev)

    def test_telemetry_and_trend_analysis_integration(self):
        metric_key = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_val = random.uniform(10.0, 99.9)

        mock_telemetry = MagicMock()
        mock_telemetry.collect.return_value = {metric_key: metric_val}

        mock_trend_analyzer = MagicMock()
        mock_trend_analyzer.analyze.return_value = {"trend": "increasing", "confidence": 0.95}

        with patch('skills.incident_auto_escalation_engine.system_health_telemetry_collector', mock_telemetry), \
             patch('skills.incident_auto_escalation_engine.incident_trend_analyzer', mock_trend_analyzer):

            report = self.engine.evaluate_system_telemetry_risks()

            mock_telemetry.collect.assert_called_once()
            mock_trend_analyzer.analyze.assert_called_once()
            self.assertIn("trend", report)
            self.assertEqual(report["risk_metric"], metric_val)

    def test_auto_patch_trigger_on_vulnerability(self):
        vuln_id = f"CVE-{random.randint(2000, 2024)}-{random.randint(1000, 9999)}"
        package_name = ''.join(random.choices(string.ascii_lowercase, k=6))

        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = [{"vulnerability_id": vuln_id, "package": package_name}]

        mock_pipeline = MagicMock()
        mock_pipeline.auto_patch_pipeline.return_value = True

        with patch('skills.incident_auto_escalation_engine.vulnerability_scanner', mock_scanner), \
             patch('skills.incident_auto_escalation_engine.auto_patch_pipeline', mock_pipeline):

            triggered = self.engine.check_and_trigger_patching()

            mock_scanner.scan.assert_called_once()
            mock_pipeline.auto_patch_pipeline.assert_called_once()
            self.assertTrue(triggered)

    def test_stream_incident_payload_reading(self):
        random_bytes = bytes(''.join(random.choices(string.printable, k=64)), 'utf-8')
        mock_stream = io.BytesIO(random_bytes)

        mock_aggregator = MagicMock()
        mock_aggregator.stream_raw_data.return_value = mock_stream

        with patch('skills.incident_auto_escalation_engine.incident_aggregator', mock_aggregator):
            consumed_data = self.engine.consume_stream_data()
            self.assertEqual(consumed_data, random_bytes)
            mock_aggregator.stream_raw_data.assert_called_once()