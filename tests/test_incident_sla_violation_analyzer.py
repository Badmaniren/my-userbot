import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.incident_sla_violation_analyzer import IncidentSLAViolationAnalyzer

class TestIncidentSLAViolationAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = IncidentSLAViolationAnalyzer()

    def test_analyze_violations_success(self):
        incident_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        limit_val = random.randint(10, 100)
        actual_val = limit_val + random.randint(1, 50)

        mock_tracker = MagicMock()
        mock_tracker.get_violations.return_value = [
            {
                "incident_id": incident_id,
                "metric": metric_name,
                "limit": limit_val,
                "actual": actual_val
            }
        ]

        with patch('skills.incident_sla_violation_analyzer.incident_sla_tracker', mock_tracker):
            result = self.analyzer.analyze_violations(incident_id)

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["incident_id"], incident_id)
            self.assertEqual(result[0]["actual"], actual_val)
            mock_tracker.get_violations.assert_called_once_with(incident_id)

    def test_analyze_violations_no_suppression(self):
        incident_id = uuid.uuid4().hex
        error_msg = ''.join(random.choices(string.ascii_letters, k=15))

        mock_tracker = MagicMock()
        mock_tracker.get_violations.side_effect = RuntimeError(error_msg)

        with patch('skills.incident_sla_violation_analyzer.incident_sla_tracker', mock_tracker):
            with self.assertRaises(RuntimeError) as ctx:
                self.analyzer.analyze_violations(incident_id)
            self.assertIn(error_msg, str(ctx.exception))

    def test_evaluate_financial_impact_integration(self):
        incident_id = uuid.uuid4().hex
        base_loss = round(random.uniform(100.5, 999.9), 2)

        mock_evaluator = MagicMock()
        mock_evaluator.calculate_loss.return_value = base_loss

        with patch('skills.incident_sla_violation_analyzer.incident_financial_impact_evaluator', mock_evaluator):
            impact = self.analyzer.evaluate_financial_impact(incident_id)

            self.assertEqual(impact, base_loss)
            mock_evaluator.calculate_loss.assert_called_once_with(incident_id)

    def test_stream_violation_report_with_bytes_io(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        mock_reporter = MagicMock()
        mock_reporter.export_stream.return_value = mock_stream

        with patch('skills.incident_sla_violation_analyzer.recovery_report_exporter', mock_reporter):
            stream_result = self.analyzer.stream_violation_report()
            data = stream_result.read()

            self.assertEqual(data, random_bytes)
            mock_reporter.export_stream.assert_called_once()

    def test_severity_escalation_trigger(self):
        incident_id = uuid.uuid4().hex
        severity_level = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = severity_level

        mock_escalation = MagicMock()

        with patch('skills.incident_sla_violation_analyzer.incident_severity_evaluator', mock_evaluator), \
             patch('skills.incident_sla_violation_analyzer.incident_auto_escalation_engine', mock_escalation):

            result = self.analyzer.check_and_escalate(incident_id)

            self.assertEqual(result, severity_level)
            mock_evaluator.evaluate.assert_called_once_with(incident_id)
            if severity_level == "CRITICAL":
                mock_escalation.trigger.assert_called_once_with(incident_id)
            else:
                mock_escalation.trigger.assert_not_called()

    def test_strict_import_consistency(self):
        import skills.incident_sla_violation_analyzer as module_under_test
        self.assertTrue(hasattr(module_under_test, 'IncidentSLAViolationAnalyzer'))

if __name__ == '__main__':
    unittest.main()