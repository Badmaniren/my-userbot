import io
import random
import uuid
import unittest
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):

    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_valid_dict(self):
        inc_id = uuid.uuid4().hex
        mock_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        
        with patch.object(self.service.incident_aggregator, "aggregate", return_value=mock_metrics) as mock_agg:
            result = self.service._fetch_incident_metrics(inc_id)
            mock_agg.assert_called_once_with(inc_id)
            self.assertEqual(result, mock_metrics)

    def test_fetch_incident_metrics_invalid_type(self):
        inc_id = uuid.uuid4().hex
        with patch.object(self.service.incident_aggregator, "aggregate", return_value=uuid.uuid4().hex):
            result = self.service._fetch_incident_metrics(inc_id)
            self.assertEqual(result, {})

    def test_fetch_recovery_logs_bytes(self):
        inc_id = uuid.uuid4().hex
        raw_logs = uuid.uuid4().hex.encode('utf-8')
        
        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=raw_logs):
            stream = self.service._fetch_recovery_logs(inc_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), raw_logs)

    def test_fetch_recovery_logs_string(self):
        inc_id = uuid.uuid4().hex
        raw_str = uuid.uuid4().hex
        
        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=raw_str):
            stream = self.service._fetch_recovery_logs(inc_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), raw_str.encode('utf-8'))

    def test_fetch_recovery_logs_invalid(self):
        inc_id = uuid.uuid4().hex
        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=random.randint(1, 500)):
            stream = self.service._fetch_recovery_logs(inc_id)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs_valid(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        content = f"\n  {line1} \n\n {line2}  \n".encode('utf-8')
        stream = io.BytesIO(content)
        
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_complex(self):
        timeout_val = random.randint(5, 50)
        metrics = {
            "memory_leak_detected": True,
            "timeout_count": timeout_val
        }
        log_line = uuid.uuid4().hex
        logs = [log_line]
        
        cause = self.service._evaluate_root_cause(metrics, logs)
        self.assertIn("Memory leak detected", cause)
        self.assertIn(str(timeout_val), cause)
        self.assertIn(log_line, cause)

    def test_generate_report_dict_input(self):
        inc_id = uuid.uuid4().hex
        err_code = uuid.uuid4().hex[:6]
        log_msg = uuid.uuid4().hex
        incident_dict = {
            "incident_id": inc_id,
            "error_code": err_code,
            "metrics": {"memory_leak_mb": random.randint(10, 500)}
        }
        recovery_data = {"logs": log_msg.encode('utf-8')}
        
        with patch.object(self.service.report_exporter, "export") as mock_export:
            report = self.service.generate_report(incident_dict, recovery_data)
            self.assertEqual(report["incident_id"], inc_id)
            self.assertIn(err_code, report["root_cause_analysis"])
            self.assertIn(log_msg, report["recovery_logs_summary"])
            mock_export.assert_called_once_with(report)

    def test_generate_report_str_input(self):
        inc_id = uuid.uuid4().hex
        mock_metrics = {uuid.uuid4().hex: random.randint(100, 999)}
        mock_logs = uuid.uuid4().hex.encode('utf-8')
        
        with patch.object(self.service, "_fetch_incident_metrics", return_value=mock_metrics) as m_met, \
             patch.object(self.service, "_fetch_recovery_logs", return_value=io.BytesIO(mock_logs)) as m_log, \
             patch.object(self.service.report_exporter, "export") as mock_export:
            
            report = self.service.generate_report(inc_id)
            m_met.assert_called_once_with(inc_id)
            m_log.assert_called_once_with(inc_id)
            self.assertEqual(report["incident_id"], inc_id)
            self.assertEqual(report["metrics_snapshot"], mock_metrics)
            mock_export.assert_called_once_with(report)

    def test_import_historical_data(self):
        id_1 = uuid.uuid4().hex
        id_2 = uuid.uuid4().hex
        batch = [{"incident_id": id_1}, {"incident_id": id_2}]
        
        with patch.object(self.service, "generate_report") as mock_gen:
            mock_gen.side_effect = lambda x: {"incident_id": x["incident_id"]}
            results = self.service.import_historical_data(batch)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["incident_id"], id_1)
            self.assertEqual(results[1]["incident_id"], id_2)
            self.assertEqual(mock_gen.call_count, 2)

    def test_export_summary_analytics(self):
        id_1 = uuid.uuid4().hex
        id_2 = uuid.uuid4().hex
        incidents = [id_1, id_2]
        
        with patch.object(self.service, "generate_report") as mock_gen:
            mock_gen.side_effect = lambda x: {"incident_id": x}
            summary = self.service.export_summary_analytics(incidents)
            
            self.assertEqual(summary["total_incidents"], 2)
            self.assertEqual(len(summary["reports_summary"]), 2)
            self.assertEqual(summary["reports_summary"][0]["incident_id"], id_1)
            self.assertEqual(summary["reports_summary"][1]["incident_id"], id_2)
            self.assertEqual(mock_gen.call_count, 2)


if __name__ == "__main__":
    unittest.main()