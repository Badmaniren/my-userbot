import io
import random
import uuid
import unittest
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):
    def setUp(self):
        with patch("skills.incident_post_mortem_service.IncidentAggregator"), \
             patch("skills.incident_post_mortem_service.ErrorRecoveryHub"), \
             patch("skills.incident_post_mortem_service.RecoveryReportExporter"):
            self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_success(self):
        inc_id = uuid.uuid4().hex
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {rand_key: rand_val}
        self.service.incident_aggregator = mock_aggregator

        result = self.service._fetch_incident_metrics(inc_id)

        mock_aggregator.aggregate.assert_called_once_with(inc_id)
        self.assertEqual(result, {rand_key: rand_val})

    def test_fetch_incident_metrics_invalid_type(self):
        inc_id = uuid.uuid4().hex
        mock_aggregator = MagicMock()
        rand_string = uuid.uuid4().hex
        mock_aggregator.aggregate.return_value = rand_string
        self.service.incident_aggregator = mock_aggregator

        result = self.service._fetch_incident_metrics(inc_id)

        self.assertEqual(result, {})

    def test_fetch_recovery_logs_bytes(self):
        inc_id = uuid.uuid4().hex
        rand_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = rand_bytes
        self.service.error_recovery_hub = mock_hub

        stream = self.service._fetch_recovery_logs(inc_id)

        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.read(), rand_bytes)

    def test_fetch_recovery_logs_string(self):
        inc_id = uuid.uuid4().hex
        rand_str = uuid.uuid4().hex
        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = rand_str
        self.service.error_recovery_hub = mock_hub

        stream = self.service._fetch_recovery_logs(inc_id)

        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.read().decode('utf-8'), rand_str)

    def test_fetch_recovery_logs_missing_attribute(self):
        inc_id = uuid.uuid4().hex
        del self.service.error_recovery_hub.get_logs

        stream = self.service._fetch_recovery_logs(inc_id)

        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        raw_data = f"  {line1} \n\n   {line2}  ".encode('utf-8')
        stream = io.BytesIO(raw_data)

        parsed = self.service._parse_recovery_logs(stream)

        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_metrics_and_logs(self):
        timeout_val = random.randint(5, 50)
        metrics = {
            "memory_leak_detected": True,
            "timeout_count": timeout_val
        }
        log_line = uuid.uuid4().hex
        logs = [log_line]

        cause = self.service._evaluate_root_cause(metrics, logs)

        self.assertIn("Memory leak detected", cause)
        self.assertIn(f"High timeout count: {timeout_val}", cause)
        self.assertIn(f"Logs analysis: {log_line}", cause)

    def test_generate_report_with_dict_and_recovery(self):
        inc_id = uuid.uuid4().hex
        error_code = f"ERR-{random.randint(1000, 9999)}"
        log_content = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(1, 100)

        incident_dict = {
            "incident_id": inc_id,
            "error_code": error_code,
            "metrics": {metric_key: metric_val, "memory_leak_detected": True}
        }
        recovery_data = {
            "logs": log_content
        }

        mock_exporter = MagicMock()
        self.service.report_exporter = mock_exporter

        report = self.service.generate_report(incident_dict, recovery_data)

        self.assertEqual(report["incident_id"], inc_id)
        self.assertIn("report_id", report)
        self.assertIn(error_code, report["root_cause_analysis"])
        self.assertIn("Memory leak detected", report["root_cause_analysis"])
        self.assertEqual(report["metrics_snapshot"][metric_key], metric_val)
        self.assertEqual(report["recovery_logs_summary"], log_content)
        mock_exporter.export.assert_called_once()

    def test_generate_report_with_string_id(self):
        inc_id = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(200, 300)
        log_bytes = uuid.uuid4().hex.encode('utf-8')

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {metric_key: metric_val}
        self.service.incident_aggregator = mock_aggregator

        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = log_bytes
        self.service.error_recovery_hub = mock_hub

        mock_exporter = MagicMock()
        self.service.report_exporter = mock_exporter

        report = self.service.generate_report(inc_id)

        self.assertEqual(report["incident_id"], inc_id)
        self.assertEqual(report["metrics_snapshot"][metric_key], metric_val)
        self.assertIn(log_bytes.decode('utf-8'), report["recovery_logs_summary"])
        mock_exporter.export.assert_called_once()

    def test_import_historical_data(self):
        inc_id_1 = uuid.uuid4().hex
        inc_id_2 = uuid.uuid4().hex
        batch = [
            {"incident_id": inc_id_1, "metrics": {}},
            {"incident_id": inc_id_2, "metrics": {}}
        ]

        with patch.object(self.service, "generate_report", wraps=self.service.generate_report) as mock_gen:
            reports = self.service.import_historical_data(batch)

            self.assertEqual(len(reports), 2)
            self.assertEqual(reports[0]["incident_id"], inc_id_1)
            self.assertEqual(reports[1]["incident_id"], inc_id_2)
            self.assertEqual(mock_gen.call_count, 2)

    def test_export_summary_analytics(self):
        inc_id = uuid.uuid4().hex
        incidents = [inc_id, {"incident_id": uuid.uuid4().hex, "metrics": {}}]

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {}
        self.service.incident_aggregator = mock_aggregator

        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = b""
        self.service.error_recovery_hub = mock_hub

        summary = self.service.export_summary_analytics(incidents)

        self.assertEqual(summary["total_incidents"], 2)
        self.assertEqual(len(summary["reports_summary"]), 2)
        self.assertEqual(summary["reports_summary"][0]["incident_id"], inc_id)


if __name__ == "__main__":
    unittest.main()