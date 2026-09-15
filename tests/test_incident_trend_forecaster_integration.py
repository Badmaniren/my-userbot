import unittest
import uuid
import random
import os
from skills.incident_trend_forecaster import IncidentTrendForecaster
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.patch_metric_collector import PatchMetricCollector

class TestIncidentTrendForecasterIntegration(unittest.TestCase):
    def setUp(self):
        self.forecaster = IncidentTrendForecaster()
        self.analyzer = IncidentTrendAnalyzer()
        self.collector = PatchMetricCollector()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.metric_value = random.uniform(0.1, 100.0)

    def test_forecast_integration_real_flow(self):
        metrics_payload = {
            "module_name": self.module_name,
            "incident_id": self.incident_id,
            "recovery_time": self.metric_value,
            "success": random.choice([True, False])
        }
        
        record_res = self.collector.record_metric(metrics_payload)
        self.assertIsInstance(record_res, dict)
        
        summary = self.collector.get_metrics_summary(self.module_name)
        self.assertIsInstance(summary, str)
        
        trends = self.analyzer.analyze_trends(self.module_name)
        
        forecast_result = self.forecaster.forecast_trends(self.module_name)
        self.assertIsNotNone(forecast_result)
        
        output_file = f"forecast_export_{uuid.uuid4().hex[:6]}.json"
        try:
            export_res = self.collector.export_metrics(output_file, "json")
            self.assertTrue(export_res)
            self.assertTrue(os.path.exists(output_file))
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)

if __name__ == "__main__":
    unittest.main()