import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_trend_forecaster import IncidentTrendForecaster
from skills import incident_trend_analyzer
from skills import patch_metric_collector


class TestIncidentTrendForecaster(unittest.TestCase):

    def setUp(self):
        self.forecaster = IncidentTrendForecaster()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10)) + "_" + uuid.uuid4().hex[:6]
        self.random_incident_id = uuid.uuid4().hex
        self.random_error_msg = f"Error_{uuid.uuid4().hex[:8]}"
        self.random_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.random_metric_val = random.randint(10, 500)

    def test_composition_imports_and_calls_analyzer(self):
        mock_trend_result = {
            "module": self.random_module,
            "trend": random.choice(["increasing", "stable", "decreasing"]),
            "risk_score": random.random(),
            "incident_count": random.randint(1, 100)
        }

        with patch('skills.incident_trend_analyzer.IncidentTrendAnalyzer') as MockAnalyzerClass:
            instance_analyzer = MockAnalyzerClass.return_value
            instance_analyzer.analyze_trends.return_value = mock_trend_result

            result = self.forecaster.forecast_future_incidents(self.random_module)

            MockAnalyzerClass.assert_called_once()
            instance_analyzer.analyze_trends.assert_called_once_with(self.random_module)
            self.assertIn(self.random_module, result.get("module_name", ""))
            self.assertEqual(result.get("trend_data"), mock_trend_result)

    def test_composition_imports_and_calls_collector(self):
        mock_metrics_summary = f"Summary_Metrics_{uuid.uuid4().hex[:8]}: {random.randint(1000, 9999)}"

        with patch('skills.patch_metric_collector.PatchMetricCollector') as MockCollectorClass:
            instance_collector = MockCollectorClass.return_value
            instance_collector.get_metrics_summary.return_value = mock_metrics_summary

            with patch.object(self.forecaster, '_extract_trends_from_analyzer', return_value={}):
                summary = self.forecaster.gather_metrics_and_trends(self.random_module)

                MockCollectorClass.assert_called_once()
                instance_collector.get_metrics_summary.assert_called_once_with(self.random_module)
                self.assertEqual(summary.get("metrics_summary"), mock_metrics_summary)

    def test_forecast_calculation_logic_with_chaos_data(self):
        chaos_incident_count = random.randint(5, 50)
        chaos_recovery_time = random.uniform(1.5, 45.0)
        
        mock_trend_payload = {
            "module_name": self.random_module,
            "incidents_history_count": chaos_incident_count,
            "average_recovery_time_seconds": chaos_recovery_time,
            "severity_weights": [random.choice([1, 2, 5, 10]) for _ in range(chaos_incident_count)]
        }

        with patch('skills.incident_trend_analyzer.IncidentTrendAnalyzer') as MockAnalyzerClass, \
             patch('skills.patch_metric_collector.PatchMetricCollector') as MockCollectorClass:
            
            MockAnalyzerClass.return_value.analyze_trends.return_value = mock_trend_payload
            MockCollectorClass.return_value.get_metrics_summary.return_value = f"Collected_{uuid.uuid4().hex}"

            forecast = self.forecaster.predict_next_failure_window(self.random_module)

            self.assertIsInstance(forecast, dict)
            self.assertIn("predicted_risk_level", forecast)
            self.assertIn("estimated_time_to_failure", forecast)
            self.assertEqual(forecast["analyzed_module"], self.random_module)
            self.assertGreaterEqual(forecast["estimated_time_to_failure"], 0.0)

    def test_stream_parsing_and_forecasting(self):
        random_stream_bytes = io.BytesIO(f"STREAM_DATA_{uuid.uuid4().hex}_METRIC_{random.randint(0, 999)}".encode('utf-8'))

        with patch('skills.incident_trend_analyzer.IncidentTrendAnalyzer') as MockAnalyzerClass:
            instance_analyzer = MockAnalyzerClass.return_value
            parsed_data_mock = {"stream_id": uuid.uuid4().hex, "status": "processed"}
            instance_analyzer.parse_stream_data.return_value = parsed_data_mock

            result = self.forecaster.process_stream_and_forecast(self.random_module, random_stream_bytes)

            instance_analyzer.parse_stream_data.assert_called_once_with(random_stream_bytes)
            self.assertEqual(result.get("stream_context"), parsed_data_mock)

    def test_export_forecasting_report(self):
        random_output_path = f"/tmp/report_{uuid.uuid4().hex}.json"
        random_format = random.choice(["json", "html", "csv"])
        mock_payload = {
            "report_id": uuid.uuid4().hex,
            "module": self.random_module,
            "prediction_confidence": random.uniform(0.7, 0.99)
        }

        with patch('skills.incident_trend_analyzer.RecoveryDashboardGenerator') as MockDashboardGen:
            instance_gen = MockDashboardGen.return_value
            instance_gen.export_dashboard.return_value = True

            success = self.forecaster.export_forecast_report(mock_payload, random_output_path, random_format)

            self.assertTrue(success)
            instance_gen.export_dashboard.assert_called_once()
            args, _ = instance_gen.export_dashboard.call_args
            self.assertEqual(args[1], random_output_path)


if __name__ == '__main__':
    unittest.main()