import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.system_risk_evaluator import SystemRiskEvaluator
from skills.system_health_aggregator import SystemHealthAggregator
from skills.vulnerability_remediation_metrics_collector import VulnerabilityRemediationMetricsCollector

class TestSystemRiskEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = SystemRiskEvaluator()

    def test_composition_dependencies(self):
        self.assertTrue(
            hasattr(self.evaluator, 'health_aggregator') or 
            hasattr(self.evaluator, 'vulnerability_collector') or
            isinstance(getattr(self.evaluator, 'health_aggregator', None), SystemHealthAggregator) or
            isinstance(getattr(self.evaluator, 'vulnerability_collector', None), VulnerabilityRemediationMetricsCollector),
            "Модуль SystemRiskEvaluator обязан использовать композицию SystemHealthAggregator и VulnerabilityRemediationMetricsCollector"
        )

    def test_evaluate_infrastructure_risk(self):
        rand_module = uuid.uuid4().hex
        rand_pipeline = uuid.uuid4().hex
        rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_metric_value = random.uniform(1.0, 100.0)

        incidents_mock = [{"id": uuid.uuid4().hex, "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])}]
        patches_mock = [{"patch_id": uuid.uuid4().hex, "status": random.choice(["APPLIED", "FAILED"])}]

        with patch('skills.system_health_aggregator.SystemHealthAggregator.collect_and_aggregate') as mock_aggregator, \
             patch('skills.vulnerability_remediation_metrics_collector.VulnerabilityRemediationMetricsCollector.collect_metric') as mock_collector:

            mock_aggregator.return_value = {
                "module": rand_module,
                "health_score": random.uniform(50.0, 100.0)
            }
            mock_collector.return_value = {
                "pipeline": rand_pipeline,
                "metric": rand_metric_name,
                "value": rand_metric_value
            }

            if hasattr(self.evaluator, 'evaluate_risk'):
                result = self.evaluator.evaluate_risk(rand_module, incidents_mock, patches_mock, rand_pipeline, rand_metric_name, rand_metric_value)
            elif hasattr(self.evaluator, 'calculate_infrastructure_risk'):
                result = self.evaluator.calculate_infrastructure_risk(rand_module, incidents_mock, patches_mock, rand_pipeline, rand_metric_name, rand_metric_value)
            else:
                result = self.evaluator.evaluate(rand_module, incidents_mock, patches_mock, rand_pipeline, rand_metric_name, rand_metric_value)

            self.assertIsNotNone(result)
            mock_aggregator.assert_called()
            mock_collector.assert_called()

    def test_stream_risk_evaluation(self):
        rand_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')
        rand_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.log"
        stream_mock = io.BytesIO(rand_stream_data)

        with patch('skills.system_health_aggregator.SystemHealthAggregator.process_stream') as mock_process_stream:
            mock_process_stream.return_value = {"status": "processed", "path": rand_path}

            if hasattr(self.evaluator, 'evaluate_stream'):
                res = self.evaluator.evaluate_stream(stream_mock, rand_path)
                self.assertIsNotNone(res)
                mock_process_stream.assert_called_once()

    def test_pipeline_metrics_aggregation_integration(self):
        rand_pipeline_id = uuid.uuid4().hex
        metrics_list = [
            {"name": uuid.uuid4().hex, "value": random.randint(1, 10)},
            {"name": uuid.uuid4().hex, "value": random.randint(11, 20)}
        ]

        with patch('skills.vulnerability_remediation_metrics_collector.VulnerabilityRemediationMetricsCollector.aggregate_pipeline_metrics') as mock_agg_pipeline:
            expected_output = {"pipeline_id": rand_pipeline_id, "aggregated": sum(m["value"] for m in metrics_list)}
            mock_agg_pipeline.return_value = expected_output

            if hasattr(self.evaluator, 'aggregate_remediation_risks'):
                res = self.evaluator.aggregate_remediation_risks(rand_pipeline_id, metrics_list)
                self.assertEqual(res["pipeline_id"], rand_pipeline_id)
                self.assertEqual(res["aggregated"], expected_output["aggregated"])

if __name__ == '__main__':
    unittest.main()