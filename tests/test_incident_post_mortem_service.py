import io
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):

    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_valid_dict(self):
        inc_id = uuid.uuid4().hex
        mock_aggregator = MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        mock_aggregator.aggregate.return_value = {rand_key: rand_val}
        self.service.incident_aggregator = mock_aggregator

        result = self.service._fetch_incident_metrics(inc_id)
        mock_aggregator.aggregate.assert_called_once_with(inc_id)
        self.assertEqual(result, {rand_key: rand_val})

    def test_fetch_incident_metrics_invalid_type(self):
        inc_id = uuid.uuid4().hex
        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = [uuid.uuid4().hex, random.randint(1, 10)]
        self.service.incident_aggregator = mock_aggregator

        result = self.service._fetch_incident_metrics(inc_id)
        self.assertEqual(result, {})

    def test_fetch_recovery_logs_bytes(self):
        inc_id = uuid.uuid4().hex
        rand_log_line = uuid.uuid4().hex.encode('utf-8')
        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = rand_log_line
        self.service.error_recovery_hub = mock_hub

        stream = self.service._fetch_recovery_logs(inc_id)
        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.read(), rand_log_line)

    def test_fetch_recovery_logs_str(self):
        inc_id = uuid.uuid4().hex
        rand_log_str = uuid.uuid4().hex
        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = rand_log_str
        self.service.error_recovery_hub = mock_hub

        stream = self.service._fetch_recovery_logs(inc_id)
        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.read(), rand_log_str.encode('utf-8'))

    def test_fetch_recovery_logs_unsupported_type(self):
        inc_id = uuid.uuid4().hex
        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = random.randint(1000, 9999)
        self.service.error_recovery_hub = mock_hub

        stream = self.service._fetch_recovery_logs(inc_id)
        self.assertIsInstance(stream, io.BytesIO)
        self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        raw_data = f"\n   {line1}   \n\n{line2}\n".encode('utf-8')
        stream = io.BytesIO(raw_data)

        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"   \n  ")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause(self):
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
        self.assertIn(log_line, cause)

    def test_generate_report_with_dict_incident(self):
        inc_id = uuid.uuid4().hex
        err_code = f"ERR-{random.randint(100, 999)}"
        log_msg = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(1, 100)

        incident_dict = {
            "incident_id": inc_id,
            "error_code": err_code,
            "metrics": {metric_key: metric_val, "memory_leak_detected": True}
        }
        recovery_data = {
            "logs": log_msg.encode('utf-8')
        }

        mock_exporter = MagicMock()
        self.service.report_exporter = mock_exporter

        report = self.service.generate_report(incident_dict, recovery_data)

        self.assertEqual(report["incident_id"], inc_id)
        self.assertIn(err_code, report["root_cause_analysis"])
        self.assertIn("Memory leak detected", report["root_cause_analysis"])
        self.assertIn(log_msg, report["recovery_logs_summary"])
        self.assertEqual(report["metrics_snapshot"], incident_dict["metrics"])
        mock_exporter.export.assert_called_once_with(report)

    def test_generate_report_with_string_incident(self):
        inc_id = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(100, 500)
        log_content = uuid.uuid4().hex

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {metric_key: metric_val}
        self.service.incident_aggregator = mock_aggregator

        mock_hub = MagicMock()
        mock_hub.get_logs.return_value = log_content.encode('utf-8')
        self.service.error_recovery_hub = mock_hub

        mock_exporter = MagicMock()
        self.service.report_exporter = mock_exporter

        report = self.service.generate_report(inc_id)

        self.assertEqual(report["incident_id"], inc_id)
        self.assertEqual(report["metrics_snapshot"], {metric_key: metric_val})
        self.assertIn(log_content, report["recovery_logs_summary"])
        mock_exporter.export.assert_called_once_with(report)


if __name__ == '__main__':
    unittest.main()