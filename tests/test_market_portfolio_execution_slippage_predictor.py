import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.market_portfolio_execution_slippage_predictor import SlippagePredictor

class TestSlippagePredictor(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_liquidity_core = MagicMock()
        self.predictor = SlippagePredictor(
            db_storage=self.mock_db,
            liquidity_core=self.mock_liquidity_core
        )

    def test_predict_slippage_calculation_logic(self):
        # Генерируем хаотичные входные данные
        asset_id = uuid.uuid4().hex
        volume = random.uniform(1000.0, 1000000.0)
        volatility = random.uniform(0.01, 0.5)
        depth = random.uniform(50000.0, 5000000.0)

        # Ожидаемый результат (логика: slippage = (vol * vol_coeff) / depth)
        expected_coeff = random.uniform(0.1, 2.0)

        with patch('skills.market_portfolio_execution_slippage_predictor.SlippagePredictor._get_historical_coeff', return_value=expected_coeff):
            result = self.predictor.predict(asset_id, volume, volatility, depth)

            expected_val = (volume * volatility * expected_coeff) / depth
            self.assertAlmostEqual(result, expected_val, places=5)

    def test_data_integrity_with_random_stream(self):
        # Проверка обработки потоковых данных из внешнего источника
        random_stream_id = uuid.uuid4().hex
        random_bytes = bytes([random.randint(0, 255) for _ in range(64)])

        with patch('skills.market_portfolio_execution_slippage_predictor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = random_bytes
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            data = self.predictor.fetch_market_depth_snapshot(random_stream_id)

            self.assertEqual(data, random_bytes)
            mock_get.assert_called_once()
            self.assertIn(random_stream_id, mock_get.call_args[0][0])

    def test_anomaly_handling_in_prediction(self):
        # Проверка реакции на аномальные входные параметры
        asset_id = uuid.uuid4().hex
        # Крайне высокое значение объема, вызывающее переполнение или исключение
        extreme_volume = float('inf')

        with self.assertRaises(ValueError):
            self.predictor.predict(asset_id, extreme_volume, 0.1, 100.0)

    def test_db_persistence_of_prediction(self):
        # Проверка записи результата в хранилище
        prediction_id = uuid.uuid4().hex
        slippage_val = random.uniform(0.001, 0.05)

        with patch.object(self.mock_db, 'save_prediction') as mock_save:
            self.predictor.save_result(prediction_id, slippage_val)

            mock_save.assert_called_once()
            args, kwargs = mock_save.call_args
            self.assertEqual(args[0], prediction_id)
            self.assertEqual(args[1], slippage_val)

    def test_liquidity_core_interaction(self):
        # Проверка взаимодействия с market_portfolio_var_liquidity_core
        ticker = ''.join(random.choices(string.ascii_uppercase, k=4))

        with patch.object(self.mock_liquidity_core, 'get_current_liquidity_score', return_value=0.99) as mock_core:
            score = self.predictor.get_liquidity_factor(ticker)

            self.assertEqual(score, 0.99)
            mock_core.assert_called_with(ticker)

if __name__ == '__main__':
    unittest.main()