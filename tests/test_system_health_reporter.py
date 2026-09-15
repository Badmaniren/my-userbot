import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
from skills.system_health_reporter import SystemHealthReporter


class TestSystemHealthReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = SystemHealthReporter()
        self.random_module = f"module_{uuid.uuid4().hex[:8]}"
        self.random_incident = f"inc_{uuid.uuid4().hex[:8]}"
        self.random_path = f"/tmp/{uuid.uuid4().hex}.json"

    def test_init_components(self):
        self.assertIsNotNone(self.reporter._aggregator)
        self.assertIsNotNone(self.reporter._exporter)

    def test_collect_system_metrics(self):
        metrics = self.reporter._collect_system_metrics(self.random_module)
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["module"], self.random_module)
        self.assertEqual(metrics["incident_id"], "")
        self.assertEqual(metrics["error"], "")
        self.assertEqual(metrics["severity"], "LOW")

    def test_generate_health_report_string_result(self):
        expected_str = f"report_{uuid.uuid4().hex}"
        with patch.object(self.reporter._aggregator, "collect_and_aggregate", return_value=expected_str) as mock_collect:
            res = self.reporter.generate_health_report(self.random_module)
            mock_collect.assert_called_once()
            self.assertEqual(res, expected_str)

    def test_generate_health_report_json_result(self):
        expected_dict = {"status": "ok", "token": uuid.uuid4().hex}
        with patch.object(self.reporter._aggregator, "collect_and_aggregate", return_value=expected_dict) as mock_collect:
            res = self.reporter.generate_health_report(self.random_module)
            mock_collect.assert_called_once()
            parsed = json.loads(res)
            self.assertEqual(parsed["status"], "ok")
            self.assertEqual(parsed["token"], expected_dict["token"])

    def test_parse_stream_data_invalid_stream(self):
        fake_stream = f"not_a_stream_{uuid.uuid4().hex}"
        res = self.reporter.parse_stream_data(fake_stream)
        self.assertIsNone(res)

    def test_parse_stream_data_valid_stream(self):
        stream_content = f'{{"id": "{uuid.uuid4().hex}"}}'.encode('utf-8')
        stream = io.BytesIO(stream_content)
        expected_parsed = {"id": "parsed"}
        with patch.object(self.reporter._aggregator, "parse_reporter_stream", return_value=expected_parsed) as mock_parse:
            res = self.reporter.parse_stream_data(stream)
            mock_parse.assert_called_once_with(stream)
            self.assertEqual(res, expected_parsed)

    def test_export_report_file(self):
        payload = {"data": uuid.uuid4().hex}
        with patch.object(self.reporter._aggregator, "save_dashboard_file", return_value=True) as mock_save:
            res = self.reporter.export_report_file(payload, self.random_path)
            mock_save.assert_called_once_with(payload, self.random_path)
            self.assertTrue(res)

    def test_export_health_report(self):
        health_report = {"health": random.choice(["GOOD", "CRITICAL"])}
        with patch.object(self.reporter._aggregator, "save_health_report", return_value=True) as mock_save:
            res = self.reporter.export_health_report(health_report, self.random_path)
            mock_save.assert_called_once_with(health_report, self.random_path)
            self.assertTrue(res)

    def test_aggregate_system_metrics(self):
        incidents = [uuid.uuid4().hex, uuid.uuid4().hex]
        patches = [uuid.uuid4().hex]
        expected_aggregated = {"total_incidents": len(incidents), "total_patches": len(patches)}
        with patch.object(self.reporter._aggregator, "aggregate_system_metrics", return_value=expected_aggregated) as mock_agg:
            res = self.reporter.aggregate_system_metrics(incidents, patches)
            mock_agg.assert_called_once_with(incidents, patches)
            self.assertEqual(res, expected_aggregated)


if __name__ == "__main__":
    unittest.main()