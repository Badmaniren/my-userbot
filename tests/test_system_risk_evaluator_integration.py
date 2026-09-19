import unittest
import uuid
import random
import os
import tempfile

from skills.system_risk_evaluator import SystemRiskEvaluator
from skills.system_health_aggregator import SystemHealthAggregator
from skills.vulnerability_remediation_metrics_collector import VulnerabilityRemediationMetricsCollector

class TestSystemRiskEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.evaluator = SystemRiskEvaluator()
        self.health_aggregator = SystemHealthAggregator()
        self.metrics_collector = VulnerabilityRemediationMetricsCollector()
        
        self.pipeline_id = str(uuid.uuid4())
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.metric_name = f"risk_metric_{random.randint(100, 999)}"
        self.metric_value = round(random.uniform(0.0, 100.0), 2)
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.temp_dir.name, f"health_report_{uuid.uuid4()}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_system_risk_evaluator_composition(self):
        self.metrics_collector.collect_metric(
            pipeline_id=self.pipeline_id,
            metric_name=self.metric_name,
            metric_value=self.metric_value
        )
        
        incidents_list = [{"id": str(uuid.uuid4()), "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])}]
        patches_list = [{"id": str(uuid.uuid4()), "status": "applied"}]
        
        health_metrics = self.health_aggregator.aggregate_system_metrics(
            incidents_list=incidents_list,
            patches_list=patches_list
        )
        
        self.assertIsInstance(health_metrics, dict)
        
        health_report = {
            "module": self.module_name,
            "pipeline_id": self.pipeline_id,
            "metrics": health_metrics,
            "custom_metric_name": self.metric_name,
            "custom_metric_value": self.metric_value
        }
        
        self.health_aggregator.save_health_report(health_report, self.report_path)
        self.assertTrue(os.path.exists(self.report_path), "Файл отчета о здоровье системы не был создан")

        risk_evaluation_result = self.evaluator.evaluate_system_risk(
            module_name=self.module_name,
            pipeline_id=self.pipeline_id,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=self.report_path
        )
        
        self.assertIsInstance(risk_evaluation_result, dict)
        self.assertIn("risk_score", risk_evaluation_result)
        self.assertIn("recommendations", risk_evaluation_result)
        
        calculated_score = risk_evaluation_result["risk_score"]
        self.assertIsInstance(calculated_score, (int, float))
        self.assertTrue(0.0 <= calculated_score <= 100.0, f"Уровень риска {calculated_score} вне диапазона [0, 100]")

if __name__ == "__main__":
    unittest.main()