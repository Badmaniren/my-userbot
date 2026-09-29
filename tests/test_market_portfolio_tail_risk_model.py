import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.market_portfolio_tail_risk_model import TailRiskModel

class TestTailRiskModel(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.model = TailRiskModel(portfolio_id=self.portfolio_id, confidence_level=self.confidence_level)

    def test_initialization_parameters(self):
        random_id = uuid.uuid4().hex
        random_conf = round(random.uniform(0.95, 0.99), 3)
        model_instance = TailRiskModel(portfolio_id=random_id, confidence_level=random_conf)
        self.assertEqual(model_instance.portfolio_id, random_id)
        self.assertEqual(model_instance.confidence_level, random_conf)

    def test_calculate_var_and_es_success(self):
        num_datapoints = random.randint(50, 200)
        returns = [random.gauss(-0.001, 0.02) for _ in range(num_datapoints)]

        var, es = self.model.calculate_var_and_es(returns)

        self.assertIsInstance(var, float)
        self.assertIsInstance(es, float)
        self.assertLessEqual(es, var)

    def test_calculate_var_and_es_empty_data(self):
        empty_returns = []
        with self.assertRaises(ValueError):
            self.model.calculate_var_and_es(empty_returns)

    def test_evaluate_historical_tail_risk_with_storage(self):
        db_identifier = uuid.uuid4().hex
        mock_storage = MagicMock()
        mock_history = [random.gauss(0.0005, 0.015) for _ in range(random.randint(30, 100))]
        mock_storage.fetch_historical_returns.return_value = mock_history

        result = self.model.evaluate_historical_tail_risk(db_storage=mock_storage, storage_key=db_identifier)

        mock_storage.fetch_historical_returns.assert_called_once_with(db_identifier)
        self.assertIn('var', result)
        self.assertIn('expected_shortfall', result)
        self.assertIn('portfolio_id', result)
        self.assertEqual(result['portfolio_id'], self.portfolio_id)

    def test_export_tail_risk_report_to_stream(self):
        random_metric_var = round(random.uniform(0.01, 0.05), 5)
        random_metric_es = round(random.uniform(random_metric_var, 0.1), 5)

        metrics = {
            'var': random_metric_var,
            'expected_shortfall': random_metric_es,
            'confidence_level': self.confidence_level,
            'token': uuid.uuid4().hex
        }

        output_buffer = io.BytesIO()

        with patch('skills.market_portfolio_tail_risk_model.sys.stdout', new=output_buffer):
            self.model.export_report(metrics)

        output_data = output_buffer.getvalue().decode('utf-8')
        self.assertIn(str(random_metric_var), output_data)
        self.assertIn(str(metrics['token']), output_data)

    def test_stress_anomaly_pipeline_integration(self):
        anomaly_payload = {
            'anomaly_id': uuid.uuid4().hex,
            'severity': random.choice(['LOW', 'MEDIUM', 'CRITICAL']),
            'drop_rate': random.uniform(0.05, 0.5)
        }

        with patch('skills.market_portfolio_tail_risk_model.market_anomaly_detector') as mock_detector:
            mock_detector.analyze_tail_event.return_value = anomaly_payload

            response = self.model.process_anomaly_trigger(anomaly_payload['anomaly_id'])

            self.assertEqual(response['anomaly_id'], anomaly_payload['anomaly_id'])
            self.assertEqual(response['status'], 'PROCESSED')

if __name__ == '__main__':
    unittest.main()