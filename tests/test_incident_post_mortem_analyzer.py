import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.incident_post_mortem_analyzer import IncidentPostMortemAnalyzer


class TestIncidentPostMortemAnalyzer(unittest.TestCase):

    def setUp(self):
        self.aggregator = MagicMock()
        self.severity_evaluator = MagicMock()
        self.trend_analyzer = MagicMock()
        self.analyzer = IncidentPostMortemAnalyzer(
            aggregator=self.aggregator,
            severity_evaluator=self.severity_evaluator,
            trend_analyzer=self.trend_analyzer
        )

    def test_analyze_incident_empty_id_raises_value_error(self):
        invalid_id = random.choice(["", None])
        with self.assertRaises(ValueError):
            self.analyzer.analyze_incident(invalid_id)

    def test_analyze_incident_valid_flow(self):
        incident_id = uuid.uuid4().hex
        expected_severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.severity_evaluator.evaluate.return_value = {"level": expected_severity}

        result = self.analyzer.analyze_incident(incident_id)

        self.assertIn("post_mortem_id", result)
        self.assertEqual(result["incident_id"], incident_id)
        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["severity"], expected_severity)
        self.assertEqual(result["root_cause"], "random_failure")
        self.severity_evaluator.evaluate.assert_called_once()
        self.aggregator.get_incident_details.assert_called_once_with(incident_id)

    def test_analyze_incident_without_evaluator_and_aggregator(self):
        analyzer_bare = IncidentPostMortemAnalyzer()
        incident_id = uuid.uuid4().hex

        result = analyzer_bare.analyze_incident(incident_id)

        self.assertEqual(result["severity"], "HIGH")
        self.assertEqual(result["incident_id"], incident_id)

    def test_analyze_empty_id_raises_value_error(self):
        invalid_id = random.choice(["", None])
        with self.assertRaises(ValueError):
            self.analyzer.analyze(invalid_id)

    def test_analyze_with_severity_info_dict(self):
        incident_id = uuid.uuid4().hex
        custom_severity = random.choice(["CRITICAL", "MODERATE", "LOW"])
        severity_info = {"severity": custom_severity}

        result = self.analyzer.analyze(incident_id, severity_info=severity_info)

        self.assertEqual(result["severity"], custom_severity)
        self.assertEqual(result["target_incident_id"], incident_id)

    def test_analyze_with_telemetry_dict(self):
        incident_id = uuid.uuid4().hex
        telemetry_data = {uuid.uuid4().hex: uuid.uuid4().hex, uuid.uuid4().hex: random.randint(1, 100)}

        result = self.analyzer.analyze(incident_id, telemetry=telemetry_data)

        self.assertIn(str(telemetry_data), result["root_cause_analysis"])
        self.assertEqual(result["target_incident_id"], incident_id)

    def test_analyze_with_system_health_telemetry_collector_duck_typing(self):
        incident_id = uuid.uuid4().hex
        mock_telemetry_collector = MagicMock()
        del mock_telemetry_collector.collect

        result = self.analyzer.analyze(incident_id, telemetry=mock_telemetry_collector)

        self.assertEqual(result["target_incident_id"], incident_id)
        self.assertEqual(result["status"], "analyzed")

    def test_generate_report_invalid_type_raises_type_error(self):
        invalid_data = random.choice([uuid.uuid4().hex, random.randint(100, 999), None, []])
        with self.assertRaises(TypeError):
            self.analyzer.generate_report(invalid_data)

    def test_generate_report_with_bytes_stream(self):
        incident_id = uuid.uuid4().hex
        random_text = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_text)

        incident_data = {
            "incident_id": incident_id,
            "stream": stream
        }

        report = self.analyzer.generate_report(incident_data)

        self.assertIn(incident_id, report)
        self.assertIn(random_text.decode('utf-8'), report)

    def test_generate_report_with_string_stream(self):
        incident_id = uuid.uuid4().hex
        random_text = uuid.uuid4().hex
        stream = io.StringIO(random_text)

        incident_data = {
            "incident_id": incident_id,
            "stream": stream
        }

        report = self.analyzer.generate_report(incident_data)

        self.assertIn(incident_id, report)
        self.assertIn(random_text, report)

    def test_generate_report_without_stream(self):
        incident_id = uuid.uuid4().hex
        incident_data = {
            "incident_id": incident_id
        }

        report = self.analyzer.generate_report(incident_data)

        self.assertIn(incident_id, report)
        self.assertIn("Stream content: ", report)