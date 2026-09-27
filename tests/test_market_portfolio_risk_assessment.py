import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json
from skills.market_portfolio_risk_assessment import PortfolioRiskAssessor

class TestPortfolioRiskAssessor(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.assessor = PortfolioRiskAssessor(db_storage=self.db_storage)

    def test_calculate_volatility_risk_logic(self):
        # Генерируем случайные исторические данные
        random_id = uuid.uuid4().hex
        random_prices = [random.uniform(10.0, 500.0) for _ in range(10)]

        # Мокаем хранилище для возврата случайных данных
        with patch.object(self.db_storage, 'get_historical_data', return_value=random_prices) as mock_db:
            risk_score = self.assessor.calculate_risk(portfolio_id=random_id)

            # Проверяем, что метод был вызван с нашим случайным ID
            mock_db.assert_called_once_with(random_id)
            # Проверяем, что результат - число (риск)
            self.assertIsInstance(risk_score, float)
            self.assertTrue(0 <= risk_score <= 1)

    def test_anomaly_detection_integration(self):
        # Генерируем случайные параметры для аномалий
        random_threshold = random.uniform(0.1, 0.9)
        random_payload = {
            "event_id": uuid.uuid4().hex,
            "severity": random.choice(['low', 'medium', 'high']),
            "value": random.random()
        }

        # Мокаем внешний сервис через patch внутри метода
        with patch('skills.market_portfolio_risk_assessment.market_anomaly_detector') as mock_detector:
            mock_detector.analyze.return_value = random_payload

            result = self.assessor.check_market_anomalies(threshold=random_threshold)

            self.assertEqual(result['event_id'], random_payload['event_id'])
            mock_detector.analyze.assert_called_once_with(threshold=random_threshold)

    def test_data_export_integrity(self):
        # Генерируем случайный путь и контент
        random_path = f"/tmp/{uuid.uuid4().hex}.json"
        random_data = {"risk_index": random.random(), "timestamp": uuid.uuid4().hex}

        # Мокаем файловую систему через mock_open
        with patch('builtins.open', unittest.mock.mock_open()) as mocked_file:
            self.assessor.export_risk_report(path=random_path, data=random_data)

            # Проверяем, что файл открывался по случайному пути
            mocked_file.assert_called_once_with(random_path, 'w')
            # Проверяем, что записанные данные содержат наш случайный ID
            handle = mocked_file()
            written_data = "".join([call.args[0] for call in handle.write.call_args_list])
            self.assertIn(random_data['timestamp'], written_data)

    def test_api_gateway_response_handling(self):
        # Генерируем случайный ответ API
        random_status = random.randint(200, 500)
        random_content = ''.join(random.choices(string.ascii_letters, k=20))

        mock_response = MagicMock()
        mock_response.status_code = random_status
        mock_response.text = random_content

        with patch('skills.market_portfolio_risk_assessment.market_portfolio_api_gateway.fetch', return_value=mock_response):
            response = self.assessor.fetch_external_metrics()

            if random_status == 200:
                self.assertEqual(response, random_content)
            else:
                self.assertIsNone(response)

    def test_stress_scenario_pipeline_execution(self):
        # Генерируем случайный сценарий
        scenario_name = uuid.uuid4().hex
        impact_factor = random.uniform(-1.0, 1.0)

        with patch('skills.market_portfolio_risk_assessment.market_portfolio_stress_scenario_pipeline') as mock_pipeline:
            mock_pipeline.run.return_value = {"status": "success", "impact": impact_factor}

            result = self.assessor.run_stress_test(scenario_name)

            self.assertEqual(result['impact'], impact_factor)
            mock_pipeline.run.assert_called_once_with(scenario_name)

if __name__ == '__main__':
    unittest.main()