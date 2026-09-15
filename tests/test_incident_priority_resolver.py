import unittest
from unittest.mock import patch
import io
import os
import uuid
import random
from skills.incident_priority_resolver import IncidentPriorityResolver, resolve_incident_priority


class TestIncidentPriorityResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = IncidentPriorityResolver()
        self.system_id = uuid.uuid4().hex

    def test_resolve_critical(self):
        trend_data = {
            "severity_score": float(random.randint(50, 100)),
            "anomaly_detected": True
        }
        with patch("skills.incident_trend_analyzer.IncidentTrendAnalyzer.analyze") as mock_analyze:
            priority = self.resolver.resolve(self.system_id, trend_data)
            mock_analyze.assert_called_once_with(trend_data)
            self.assertEqual(priority, "CRITICAL")

    def test_resolve_high(self):
        trend_data = {
            "severity_score": float(random.randint(31, 49)),
            "anomaly_detected": False
        }
        with patch("skills.incident_trend_analyzer.IncidentTrendAnalyzer.analyze") as mock_analyze:
            priority = self.resolver.resolve(self.system_id, trend_data)
            mock_analyze.assert_called_once_with(trend_data)
            self.assertEqual(priority, "HIGH")

    def test_resolve_medium(self):
        trend_data = {
            "severity_score": float(random.randint(15, 30)),
            "anomaly_detected": False
        }
        with patch("skills.incident_trend_analyzer.IncidentTrendAnalyzer.analyze") as mock_analyze:
            priority = self.resolver.resolve(self.system_id, trend_data)
            mock_analyze.assert_called_once_with(trend_data)
            self.assertEqual(priority, "MEDIUM")

    def test_resolve_low(self):
        trend_data = {
            "severity_score": float(random.randint(0, 14)),
            "anomaly_detected": False
        }
        with patch("skills.incident_trend_analyzer.IncidentTrendAnalyzer.analyze") as mock_analyze:
            priority = self.resolver.resolve(self.system_id, trend_data)
            mock_analyze.assert_called_once_with(trend_data)
            self.assertEqual(priority, "LOW")

    def test_evaluate_stream(self):
        rand_code = f"ERR_{random.randint(1000, 9999)}"
        stream_content = f"timestamp=now|CODE:{rand_code}|status=failed".encode('utf-8')
        mock_gateway = type("GatewayMock", (), {
            "stream_logs": lambda self, sys_id: io.BytesIO(stream_content)
        })()

        result = self.resolver.evaluate_stream(mock_gateway, self.system_id)
        self.assertEqual(result["system_id"], self.system_id)
        self.assertEqual(result["error_code"], rand_code)
        self.assertEqual(result["priority"], "MEDIUM")

    def test_calculate_from_forecast_critical(self):
        load_val = random.randint(85, 100)
        with patch("skills.incident_trend_forecaster.IncidentTrendForecaster.predict_next_spike") as mock_predict:
            mock_predict.return_value = {"predicted_load": load_val}
            priority = self.resolver.calculate_from_forecast(self.system_id)
            mock_predict.assert_called_once_with(self.system_id)
            self.assertEqual(priority, "CRITICAL")

    def test_calculate_from_forecast_high(self):
        load_val = random.randint(70, 84)
        with patch("skills.incident_trend_forecaster.IncidentTrendForecaster.predict_next_spike") as mock_predict:
            mock_predict.return_value = {"predicted_load": load_val}
            priority = self.resolver.calculate_from_forecast(self.system_id)
            mock_predict.assert_called_once_with(self.system_id)
            self.assertEqual(priority, "HIGH")

    def test_calculate_from_forecast_medium(self):
        load_val = random.randint(0, 69)
        with patch("skills.incident_trend_forecaster.IncidentTrendForecaster.predict_next_spike") as mock_predict:
            mock_predict.return_value = {"predicted_load": load_val}
            priority = self.resolver.calculate_from_forecast(self.system_id)
            mock_predict.assert_called_once_with(self.system_id)
            self.assertEqual(priority, "MEDIUM")


class TestResolveIncidentPriorityStandalone(unittest.TestCase):

    def setUp(self):
        self.incident_id = uuid.uuid4().hex

    def tearDown(self):
        report_path = f"report_{self.incident_id}.txt"
        if os.path.exists(report_path):
            os.remove(report_path)

    def test_resolve_incident_priority_critical_anomaly(self):
        trend_data = {
            "severity_score": float(random.randint(0, 100)),
            "anomaly_detected": True
        }
        res = resolve_incident_priority(self.incident_id, trend_data)
        self.assertEqual(res["target_incident_id"], self.incident_id)
        self.assertEqual(res["priority_level"], "CRITICAL")
        self.assertTrue(os.path.exists(res["report_file_path"]))

    def test_resolve_incident_priority_high(self):
        trend_data = {
            "severity_score": float(random.randint(41, 70)),
            "anomaly_detected": False
        }
        res = resolve_incident_priority(self.incident_id, trend_data)
        self.assertEqual(res["target_incident_id"], self.incident_id)
        self.assertEqual(res["priority_level"], "HIGH")
        self.assertTrue(os.path.exists(res["report_file_path"]))

    def test_resolve_incident_priority_medium(self):
        trend_data = {
            "severity_score": float(random.randint(21, 40)),
            "anomaly_detected": False
        }
        res = resolve_incident_priority(self.incident_id, trend_data)
        self.assertEqual(res["target_incident_id"], self.incident_id)
        self.assertEqual(res["priority_level"], "MEDIUM")
        self.assertTrue(os.path.exists(res["report_file_path"]))

    def test_resolve_incident_priority_low(self):
        trend_data = {
            "severity_score": float(random.randint(0, 20)),
            "anomaly_detected": False
        }
        res = resolve_incident_priority(self.incident_id, trend_data)
        self.assertEqual(res["target_incident_id"], self.incident_id)
        self.assertEqual(res["priority_level"], "LOW")
        self.assertTrue(os.path.exists(res["report_file_path"]))
        with open(res["report_file_path"], "r") as f:
            content = f.read()
            self.assertIn(self.incident_id, content)
            self.assertIn("LOW", content)


if __name__ == '__main__':
    unittest.main()