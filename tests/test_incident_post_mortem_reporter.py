import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
import datetime
from skills.incident_post_mortem_reporter import (
    IncidentPostMortemReporter,
    generate_incident_post_mortem
)

class TestIncidentPostMortemReporter(unittest.TestCase):
    def test_incident_post_mortem_reporter_initialization_and_generation(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        summary = uuid.uuid4().hex
        recurrence_score = random.randint(1, 100)

        mock_aggregator = unittest.mock.MagicMock()
        mock_aggregator.get_aggregated_incident.return_value = {
            "id": incident_id,
            "severity": severity,
            "summary": summary
        }

        mock_trend_analyzer = unittest.mock.MagicMock()
        mock_trend_analyzer.analyze_trend.return_value = {
            "recurrence_score": recurrence_score
        }

        reporter = IncidentPostMortemReporter(mock_aggregator, mock_trend_analyzer)
        reporter.trend_analyzer = mock_trend_analyzer

        report = reporter.generate(incident_id)

        mock_aggregator.get_aggregated_incident.assert_called_once_with(incident_id)
        mock_trend_analyzer.analyze_trend.assert_called_once()

        self.assertEqual(report["incident_id"], incident_id)
        self.assertEqual(report["severity"], severity)
        self.assertEqual(report["summary"], summary)
        self.assertEqual(report["trend_score"], recurrence_score)
        self.assertIn("generated_at", report)

    def test_incident_post_mortem_reporter_export_to_stream(self):
        incident_id = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        summary = uuid.uuid4().hex
        recurrence_score = random.randint(10, 500)

        mock_aggregator = unittest.mock.MagicMock()
        mock_aggregator.get_aggregated_incident.return_value = {
            "id": incident_id,
            "severity": severity,
            "summary": summary
        }

        mock_trend_analyzer = unittest.mock.MagicMock()
        mock_trend_analyzer.analyze_trend.return_value = {
            "recurrence_score": recurrence_score
        }

        reporter = IncidentPostMortemReporter(mock_aggregator, mock_trend_analyzer)
        reporter.trend_analyzer = mock_trend_analyzer

        stream = io.BytesIO()
        written_len = reporter.export_to_stream(incident_id, stream)

        stream.seek(0)
        content = stream.read()
        self.assertEqual(len(content), written_len)

        parsed = json.loads(content.decode("utf-8"))
        self.assertEqual(parsed["incident_id"], incident_id)
        self.assertEqual(parsed["trend_score"], recurrence_score)

    def test_generate_incident_post_mortem_function(self):
        system_id = uuid.uuid4().hex
        aggregated_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        trend_analysis = {uuid.uuid4().hex: random.randint(1, 100)}
        output_path = f"{uuid.uuid4().hex}.json"

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = generate_incident_post_mortem(system_id, aggregated_data, trend_analysis, output_path)

        mock_file.assert_called_once_with(output_path, "w", encoding="utf-8")
        self.assertEqual(result["system_id"], system_id)
        self.assertEqual(result["aggregated_data"], aggregated_data)
        self.assertEqual(result["trend_analysis"], trend_analysis)
        self.assertIn("report_id", result)
        self.assertIn("generated_at", result)

if __name__ == "__main__":
    unittest.main()