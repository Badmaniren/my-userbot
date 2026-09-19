import unittest
import uuid
import random
import os
from skills.incident_predictive_risk_model import incident_predictive_risk_model
from skills.system_health_aggregator import system_health_aggregator
from skills.incident_trend_analyzer import incident_trend_analyzer
from skills.incident_severity_evaluator import incident_severity_evaluator

class TestIncidentPredictiveRiskModelIntegration(unittest.TestCase):
    def test_predictive_risk_model_end_to_end_flow(self):
        unique_system_id = f"sys-{uuid.uuid4()}"
        random_metric_value = round(random.uniform(10.5, 99.9), 2)
        test_payload = {
            "system_id": unique_system_id,
            "telemetry_metric": random_metric_value,
            "node_status": random.choice(["active", "degraded", "volatile"]),
            "historical_window_days": random.randint(7, 90)
        }

        health_data = system_health_aggregator(test_payload)
        
        trend_input = {
            "health_aggregate": health_data,
            "evaluation_depth": random.randint(1, 5)
        }
        trend_analysis = incident_trend_analyzer(trend_input)

        severity_input = {
            "trend_data": trend_analysis,
            "threshold_factor": random.random()
        }
        severity_evaluation = incident_severity_evaluator(severity_input)

        predictive_input = {
            "system_id": unique_system_id,
            "health_aggregate": health_data,
            "trend_analysis": trend_analysis,
            "severity_evaluation": severity_evaluation,
            "simulation_seed": random.randint(1000, 9999)
        }

        result = incident_predictive_risk_model(predictive_input)

        self.assertIsInstance(result, dict, "Результат должен быть словарем")
        self.assertIn("risk_assessment_id", result, "Должен быть сгенерирован ID оценки риска")
        self.assertEqual(result.get("target_system_id"), unique_system_id, "ID системы в ответе должен совпадать со сгенерированным")
        self.assertIn("predicted_risk_score", result, "Должен присутствовать расчетный балл риска")
        self.assertIsInstance(result["predicted_risk_score"], (int, float), "Балл риска должен быть числовым")

        artifact_path = f"/tmp/risk_report_{unique_system_id}.json"
        if os.path.exists(artifact_path):
            self.assertTrue(os.path.getsize(artifact_path) > 0, "Артефакт отчета о рисках не должен быть пустым")

if __name__ == "__main__":
    unittest.main()