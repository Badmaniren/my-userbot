import io
import random
import uuid
import unittest
from unittest.mock import MagicMock, patch

from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemService(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()

    def test_fetch_incident_metrics_success(self):
        incident_id = uuid.uuid4().hex
        mock_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        
        with patch.object(self.service.incident_aggregator, "aggregate", return_value=mock_metrics) as mock_agg:
            result = self.service._fetch_incident_metrics(incident_id)
            mock_agg.assert_called_once_with(incident_id)
            self.assertEqual(result, mock_metrics)

    def test_fetch_incident_metrics_invalid_type(self):
        incident_id = uuid.uuid4().hex
        with patch.object(self.service.incident_aggregator, "aggregate", return_value=uuid.uuid4().hex):
            result = self.service._fetch_incident_metrics(incident_id)
            self.assertEqual(result, {})

    def test_fetch_recovery_logs_bytes(self):
        incident_id = uuid.uuid4().hex
        log_content = uuid.uuid4().hex.encode('utf-8')
        
        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=log_content) as mock_logs:
            stream = self.service._fetch_recovery_logs(incident_id)
            mock_logs.assert_called_once_with(incident_id)
            self.assertEqual(stream.read(), log_content)

    def test_fetch_recovery_logs_string(self):
        incident_id = uuid.uuid4().hex
        log_str = uuid.uuid4().hex
        
        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=log_str):
            stream = self.service._fetch_recovery_logs(incident_id)
            self.assertEqual(stream.read().decode('utf-8'), log_str)

    def test_fetch_recovery_logs_fallback(self):
        incident_id = uuid.uuid4().hex
        with patch.object(self.service.error_recovery_hub, "get_logs", return_value=random.randint(1, 100)):
            stream = self.service._fetch_recovery_logs(incident_id)
            self.assertEqual(stream.read(), b"")

    def test_parse_recovery_logs(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        raw_data = f"  {line1} \n\n {line2}  ".encode('utf-8')
        stream = io.BytesIO(raw_data)
        
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [line1, line2])

    def test_parse_recovery_logs_empty(self):
        stream = io.BytesIO(b"")
        parsed = self.service._parse_recovery_logs(stream)
        self.assertEqual(parsed, [])

    def test_evaluate_root_cause_comprehensive(self):
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

    def test_generate_report_with_dict_incident(self):
        incident_id = uuid.uuid4().hex
        error_code = uuid.uuid4().hex[:8]
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(100, 999)
        log_text = uuid.uuid4().hex
        
        incident_data = {
            "incident_id": incident_id,
            "metrics": {metric_key: metric_val, "memory_leak_mb": random.randint(1, 10)},
            "error_code": error_code
        }
        recovery_data = {
            "logs": log_text.encode('utf-8')
        }
        
        with patch.object(self.service.report_exporter, "export") as mock_export:
            report = self.service.generate_report(incident_data, recovery_data)
            
            mock_export.assert_called_once()
            self.assertEqual(report["incident_id"], incident_id)
            self.assertIn(error_code, report["root_cause_analysis"])
            self.assertIn("Memory leak detected", report["root_cause_analysis"])
            self.assertEqual(report["metrics_snapshot"][metric_key], metric_val)
            self.assertEqual(report["recovery_logs_summary"], log_text)

    def test_generate_report_with_string_incident(self):
        incident_id = uuid.uuid4().hex
        mock_metrics = {uuid.uuid4().hex: uuid.uuid4().hex}
        log_data = uuid.uuid4().hex.encode('utf-8')
        
        with patch.object(self.service, "_fetch_incident_metrics", return_value=mock_metrics) as mock_m, \
             patch.object(self.service, "_fetch_recovery_logs", return_value=io.BytesIO(log_data)) as mock_l, \
             patch.object(self.service.report_exporter, "export") as mock_export:
            
            report = self.service.generate_report(incident_id)
            
            mock_m.assert_called_once_with(incident_id)
            mock_l.assert_called_once_with(incident_id)
            mock_export.assert_called_once()
            self.assertEqual(report["incident_id"], incident_id)
            self.assertEqual(report["metrics_snapshot"], mock_metrics)
            self.assertEqual(report["recovery_logs_summary"], log_data.decode('utf-8'))

    def test_import_historical_data(self):
        inc1_id = uuid.uuid4().hex
        inc2_id = uuid.uuid4().hex
        batch = [
            {"incident_id": inc1_id, "metrics": {}},
            {"incident_id": inc2_id, "metrics": {}}
        ]
        
        with patch.object(self.service, "generate_report", side_effect=lambda x: {"incident_id": x["incident_id"]}):
            reports = self.service.import_historical_data(batch)
            self.assertEqual(len(reports), 2)
            self.assertEqual(reports[0]["incident_id"], inc1_id)
            self.assertEqual(reports[1]["incident_id"], inc2_id)

    def test_export_summary_analytics(self):
        inc_id = uuid.uuid4().hex
        incidents = [inc_id]
        mock_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        with patch.object(self.service, "generate_report", return_value=mock_report) as mock_gen:
            summary = self.service.export_summary_analytics(incidents)
            mock_gen.assert_called_once_with(inc_id)
            self.assertEqual(summary["total_incidents"], 1)
            self.assertEqual(summary["reports_summary"], [mock_report])


if __name__ == "__main__":
    unittest.main()