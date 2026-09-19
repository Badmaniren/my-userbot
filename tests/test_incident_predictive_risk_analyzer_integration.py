import unittest
import uuid
import random
import os
import tempfile
from skills.incident_predictive_risk_analyzer import incident_predictive_risk_analyzer
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.incident_aggregator import incident_aggregator
from skills.incident_trend_analyzer import incident_trend_analyzer

class TestIncidentPredictiveRiskAnalyzerIntegration(unittest.TestCase):
    def test_predictive_risk_analyzer_integration(self):
        unique_incident_id = f"inc-{uuid.uuid4()}"
        random_metric_value = round(random.uniform(10.0, 99.9), 2)
        
        telemetry_payload = {
            "source": "integration_test_telemetry",
            "metric_name": "cpu_load",
            "value": random_metric_value,
            "unit": "percent"
        }
        
        telemetry_result = system_health_telemetry_collector(telemetry_payload)
        self.assertIsNotNone(telemetry_result)

        incident_payload = {
            "incident_id": unique_incident_id,
            "severity": "HIGH",
            "description": "Integration test generated incident for predictive analysis"
        }
        
        aggregation_result = incident_aggregator(incident_payload)
        self.assertIsNotNone(aggregation_result)

        trend_payload = {
            "incident_id": unique_incident_id,
            "timeframe": "24h"
        }
        
        trend_result = incident_trend_analyzer(trend_payload)
        self.assertIsNotNone(trend_result)

        analysis_context = {
            "incident_id": unique_incident_id,
            "telemetry_data": telemetry_result,
            "trend_data": trend_result,
            "risk_threshold": random.randint(50, 90)
        }

        risk_analysis_output = incident_predictive_risk_analyzer(analysis_context)

        self.assertIsInstance(risk_analysis_output, dict)
        self.assertIn("risk_score", risk_analysis_output)
        self.assertIn("predicted_failure_probability", risk_analysis_output)
        
        output_file_path = f"risk_report_{unique_incident_id}.json"
        if os.path.exists(output_file_path):
            self.assertTrue(os.path.getsize(output_file_path) > 0)
            os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()