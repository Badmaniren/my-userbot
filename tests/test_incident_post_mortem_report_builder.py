import unittest
from unittest.mock import MagicMock, patch
import io
import json
import uuid
import random
import string

from skills.incident_post_mortem_report_builder import (
    IncidentPostMortemReportBuilder,
    incident_post_mortem_report_builder
)

class TestIncidentPostMortemReportBuilder(unittest.TestCase):

    def setUp(self):
        self.mock_aggregator = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_trend_analyzer = MagicMock()
        self.mock_telemetry_collector = MagicMock()

        self.builder = IncidentPostMortemReportBuilder(
            incident_aggregator=self.mock_aggregator,
            incident_severity_evaluator=self.mock_evaluator,
            incident_trend_analyzer=self.mock_trend_analyzer,
            system_health_telemetry_collector=self.mock_telemetry_collector
        )

        self.incident_id = str(uuid.uuid4())
        self.random_string = ''.join(random.choices(string.ascii_letters, k=12))
        self.random_metric = random.randint(100, 9999)

    def test_build_report_success(self):
        expected_incident = {"id": self.incident_id, "detail": self.random_string}
        expected_severity = {"score": self.random_metric}
        expected_trend = {"status": self.random_string}
        expected_telemetry = {"uptime": self.random_metric}

        self.mock_aggregator.get_incident.return_value = expected_incident
        self.mock_evaluator.evaluate.return_value = expected_severity
        self.mock_trend_analyzer.analyze.return_value = expected_trend
        self.mock_telemetry_collector.collect.return_value = expected_telemetry

        report = self.builder.build_report(self.incident_id)

        self.assertEqual(report["incident_details"], expected_incident)
        self.assertEqual(report["severity_assessment"], expected_severity)
        self.assertEqual(report["trend_analysis"], expected_trend)
        self.assertEqual(report["system_telemetry"], expected_telemetry)

        self.mock_aggregator.get_incident.assert_called_once_with(self.incident_id)
        self.mock_evaluator.evaluate.assert_called_once_with(expected_incident)
        self.mock_trend_analyzer.analyze.assert_called_once_with(expected_incident)
        self.mock_telemetry_collector.collect.assert_called_once()

    def test_build_report_not_found(self):
        self.mock_aggregator.get_incident.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.builder.build_report(self.incident_id)

        self.assertIn(self.incident_id, str(ctx.exception))
        self.mock_aggregator.get_incident.assert_called_once_with(self.incident_id)
        self.mock_evaluator.evaluate.assert_not_called()
        self.mock_trend_analyzer.analyze.assert_not_called()
        self.mock_telemetry_collector.collect.assert_not_called()

    def test_export_report_stream(self):
        expected_incident = {"id": self.incident_id, "detail": self.random_string}
        expected_severity = {"score": self.random_metric}
        expected_trend = {"status": self.random_string}
        expected_telemetry = {"uptime": self.random_metric}

        self.mock_aggregator.get_incident.return_value = expected_incident
        self.mock_evaluator.evaluate.return_value = expected_severity
        self.mock_trend_analyzer.analyze.return_value = expected_trend
        self.mock_telemetry_collector.collect.return_value = expected_telemetry

        stream = io.BytesIO()
        result_stream = self.builder.export_report_stream(self.incident_id, stream)

        self.assertEqual(result_stream, stream)
        stream.seek(0)
        content_bytes = stream.read()
        parsed_data = json.loads(content_bytes.decode('utf-8'))

        self.assertEqual(parsed_data["incident_details"]["id"], self.incident_id)
        self.assertEqual(parsed_data["incident_details"]["detail"], self.random_string)
        self.assertEqual(parsed_data["severity_assessment"]["score"], self.random_metric)
        self.assertEqual(parsed_data["trend_analysis"]["status"], self.random_string)
        self.assertEqual(parsed_data["system_telemetry"]["uptime"], self.random_metric)


class TestIncidentPostMortemReportBuilderIntegration(unittest.TestCase):

    def test_incident_post_mortem_report_builder_function(self):
        rnd_key = ''.join(random.choices(string.ascii_lowercase, k=8))
        rnd_val = ''.join(random.choices(string.ascii_letters, k=10))

        data = {
            "incident": {rnd_key: rnd_val},
            "severity": {"level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])},
            "trend": {"direction": random.choice(["UP", "DOWN", "FLAT"])},
            "health": {"cpu_load": random.random() * 100}
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            result = incident_post_mortem_report_builder(data)

            self.assertIn("report_id", result)
            self.assertIn("file_path", result)
            self.assertEqual(result["incident_details"], data["incident"])
            self.assertEqual(result["severity_assessment"], data["severity"])
            self.assertEqual(result["trend_analysis"], data["trend"])
            self.assertEqual(result["system_telemetry"], data["health"])

            mock_file.assert_called_once()
            handle = mock_file()
            handle.write.assert_called()


if __name__ == '__main__':
    unittest.main()