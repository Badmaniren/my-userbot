import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string
from skills.market_stress_risk_aggregator import MarketStressRiskAggregator

class TestMarketStressRiskAggregator(unittest.TestCase):

    def setUp(self):
        self.mock_monte_carlo = MagicMock()
        self.mock_scenario_matrix = MagicMock()
        self.aggregator = MarketStressRiskAggregator(
            monte_carlo_engine=self.mock_monte_carlo,
            scenario_evaluator=self.mock_scenario_matrix
        )

    def test_aggregate_risk_profile_integrity(self):
        # Генерируем случайные данные для проверки целостности
        random_portfolio_id = uuid.uuid4().hex
        random_var = random.uniform(0.01, 0.99)
        random_scenario_impact = random.uniform(-1000, 1000)

        # Настройка поведения моков
        self.mock_monte_carlo.calculate_var.return_value = random_var
        self.mock_scenario_matrix.evaluate.return_value = {"impact": random_scenario_impact}

        # Выполнение
        result = self.aggregator.aggregate(random_portfolio_id)

        # Проверка: данные должны соответствовать сгенерированным
        self.assertEqual(result['portfolio_id'], random_portfolio_id)
        self.assertEqual(result['var_value'], random_var)
        self.assertEqual(result['scenario_impact'], random_scenario_impact)
        self.assertIn('timestamp', result)

    def test_normalization_logic_with_random_noise(self):
        # Генерируем случайный набор данных для нормализации
        raw_data = [random.uniform(10, 1000) for _ in range(5)]
        expected_norm = sum(raw_data) / len(raw_data)

        with patch('skills.market_stress_risk_aggregator.MarketStressRiskAggregator._normalize') as mock_norm:
            mock_norm.return_value = expected_norm

            result = self.aggregator.normalize_risk_metrics(raw_data)

            self.assertEqual(result, expected_norm)
            mock_norm.assert_called_once_with(raw_data)

    def test_stress_report_generation_io(self):
        # Генерируем случайный контент для отчета
        random_content = ''.join(random.choices(string.ascii_letters, k=50))
        random_filename = f"{uuid.uuid4().hex}.log"

        # Используем io.BytesIO для имитации файлового потока
        mock_file_stream = io.BytesIO()
        mock_file_stream.close = MagicMock()

        with patch('builtins.open', return_value=mock_file_stream) as mock_open:
            self.aggregator.export_stress_report(random_filename, content=random_content)

            mock_open.assert_called_with(random_filename, 'w')
            self.assertEqual(mock_file_stream.getvalue().decode('utf-8'), random_content)

    def test_anomaly_threshold_trigger(self):
        # Генерируем случайный порог и значение риска
        threshold = random.uniform(0.5, 0.8)
        risk_value = threshold + random.uniform(0.1, 0.2)

        self.mock_monte_carlo.get_current_risk.return_value = risk_value

        # Проверяем, что агрегатор корректно определяет превышение
        is_critical = self.aggregator.check_critical_stress(threshold)

        self.assertTrue(is_critical)
        self.mock_monte_carlo.get_current_risk.assert_called_once()

    def test_dependency_injection_validation(self):
        # Проверка на случайные объекты-заглушки
        random_obj_1 = MagicMock()
        random_obj_2 = MagicMock()

        aggregator = MarketStressRiskAggregator(random_obj_1, random_obj_2)

        self.assertEqual(aggregator.monte_carlo_engine, random_obj_1)
        self.assertEqual(aggregator.scenario_evaluator, random_obj_2)

if __name__ == '__main__':
    unittest.main()