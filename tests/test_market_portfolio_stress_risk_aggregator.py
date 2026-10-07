import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json
from skills.market_portfolio_stress_risk_aggregator import StressRiskAggregator

class TestStressRiskAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = StressRiskAggregator()
        self.random_id = uuid.uuid4().hex
        self.random_val = random.uniform(0.01, 0.99)

    def test_aggregate_monte_carlo_results(self):
        # Генерируем случайные данные для симуляции
        mock_data = {
            "scenario_id": uuid.uuid4().hex,
            "var_95": random.uniform(1000, 5000),
            "cvar_95": random.uniform(5000, 10000),
            "timestamp": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_stress_monte_carlo_engine.get_latest_results') as mock_engine:
            mock_engine.return_value = mock_data

            result = self.aggregator.aggregate(mock_data["scenario_id"])

            self.assertEqual(result['id'], mock_data["scenario_id"])
            self.assertGreater(result['var'], 0)
            self.assertEqual(result['var'], mock_data["var_95"])

    def test_data_integrity_with_io_stream(self):
        # Проверка обработки потоковых данных (имитация чтения из хранилища)
        random_content = f'{{"risk_score": {random.random()}}}'.encode('utf-8')
        mock_stream = io.BytesIO(random_content)

        with patch('skills.db_storage.open_stream') as mock_db:
            mock_db.return_value = mock_stream

            data = self.aggregator.fetch_raw_metrics(uuid.uuid4().hex)
            self.assertIn('risk_score', data)
            self.assertIsInstance(data['risk_score'], float)

    def test_aggregation_logic_failure_handling(self):
        # Проверка на случайный сбой в движке
        bad_id = uuid.uuid4().hex
        with patch('skills.market_portfolio_stress_monte_carlo_engine.get_latest_results') as mock_engine:
            mock_engine.side_effect = Exception("Engine Failure")

            with self.assertRaises(RuntimeError):
                self.aggregator.aggregate(bad_id)

    def test_quantiles_calculation_accuracy(self):
        # Проверка корректности агрегации нескольких квантилей
        scenario_id = uuid.uuid4().hex
        mock_metrics = [
            {"q": 0.95, "val": random.uniform(10, 20)},
            {"q": 0.99, "val": random.uniform(20, 30)}
        ]

        with patch('skills.market_portfolio_stress_monte_carlo_engine.get_quantiles') as mock_quantiles:
            mock_quantiles.return_value = mock_metrics

            aggregated = self.aggregator.process_quantiles(scenario_id)

            # Проверяем, что агрегатор правильно пробросил случайные значения
            self.assertEqual(len(aggregated), 2)
            self.assertEqual(aggregated[0]['q'], 0.95)
            self.assertEqual(aggregated[1]['val'], mock_metrics[1]['val'])

    def test_visualization_bridge_call(self):
        # Проверка передачи данных в визуализатор
        target_id = uuid.uuid4().hex
        payload = {"data": [random.random() for _ in range(5)]}

        with patch('skills.market_portfolio_stress_audit_visualizer.render') as mock_viz:
            mock_viz.return_value = True

            status = self.aggregator.push_to_visualizer(target_id, payload)

            self.assertTrue(status)
            mock_viz.assert_called_once()
            # Проверяем, что передан именно наш случайный ID
            args, _ = mock_viz.call_args
            self.assertEqual(args[0], target_id)

if __name__ == '__main__':
    unittest.main()