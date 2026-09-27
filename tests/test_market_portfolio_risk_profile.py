import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string
from skills.market_portfolio_risk_profile import RiskProfileCalculator

class TestMarketPortfolioRiskProfile(unittest.TestCase):

    def setUp(self):
        self.calculator = RiskProfileCalculator()

    def test_calculate_volatility_score_logic(self):
        # Генерируем случайные данные для активов
        asset_count = random.randint(5, 20)
        mock_data = {
            f"ASSET_{uuid.uuid4().hex[:8]}": random.uniform(0.01, 0.5)
            for _ in range(asset_count)
        }

        # Вызываем метод
        result = self.calculator.calculate_volatility_score(mock_data)

        # Проверяем, что результат находится в ожидаемом диапазоне (0-1)
        self.assertTrue(0 <= result <= 1, f"Score {result} out of bounds")
        self.assertIsInstance(result, float)

    def test_risk_profile_classification(self):
        # Генерируем случайный порог волатильности
        random_score = random.uniform(0, 1)

        # Проверяем логику классификации
        profile = self.calculator.classify_risk(random_score)

        self.assertIn(profile, ["CONSERVATIVE", "MODERATE", "AGGRESSIVE"])

    def test_data_extraction_integration(self):
        # Генерируем случайный URL и ID
        random_url = f"https://api.market.data/{uuid.uuid4().hex}"
        random_id = uuid.uuid4().hex

        # Мокаем запрос через requests
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Генерируем случайный JSON-ответ
            mock_response.json.return_value = {
                "id": random_id,
                "volatility": random.random()
            }
            mock_get.return_value = mock_response

            result = self.calculator.fetch_and_analyze(random_url)

            # Проверяем, что ID совпадает с тем, что мы "получили" из сети
            self.assertEqual(result['id'], random_id)
            mock_get.assert_called_once_with(random_url)

    def test_audit_log_generation(self):
        # Генерируем случайные параметры для аудита
        random_user = ''.join(random.choices(string.ascii_letters, k=10))
        random_action = uuid.uuid4().hex

        with patch('skills.market_portfolio_risk_profile.market_portfolio_audit_log_exporter') as mock_exporter:
            self.calculator.log_risk_event(random_user, random_action)

            # Проверяем, что логгер был вызван с нашими случайными данными
            mock_exporter.export.assert_called_once()
            args, _ = mock_exporter.export.call_args
            self.assertIn(random_user, str(args))
            self.assertIn(random_action, str(args))

    def test_stress_scenario_handling(self):
        # Генерируем случайный сценарий
        scenario_name = f"SCENARIO_{uuid.uuid4().hex[:5]}"
        shock_value = random.uniform(-0.5, -0.1)

        with patch('skills.market_portfolio_risk_profile.market_portfolio_stress_scenario_pipeline') as mock_pipeline:
            mock_pipeline.run.return_value = {"status": "COMPLETED", "impact": shock_value}

            result = self.calculator.simulate_stress(scenario_name)

            self.assertEqual(result['impact'], shock_value)
            self.assertEqual(result['status'], "COMPLETED")

    def test_invalid_data_handling(self):
        # Проверка на пустые данные
        empty_data = {}
        with self.assertRaises(ValueError):
            self.calculator.calculate_volatility_score(empty_data)

    def test_stream_processing(self):
        # Имитация чтения потока данных
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_risk_profile.market_parser') as mock_parser:
            mock_parser.parse_stream.return_value = {"data": "processed"}

            result = self.calculator.process_raw_stream(mock_stream)
            self.assertEqual(result['data'], "processed")
            self.assertTrue(mock_parser.parse_stream.called)

if __name__ == '__main__':
    unittest.main()