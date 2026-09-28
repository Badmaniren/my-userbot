import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_hedge_trigger import HedgeTrigger

class TestMarketPortfolioHedgeTrigger(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_analytics = MagicMock()
        self.trigger = HedgeTrigger(
            db_storage=self.mock_db,
            market_portfolio_performance_analytics=self.mock_analytics
        )

    def test_hedge_activation_logic(self):
        # Генерируем случайные пороговые значения и метрики
        var_threshold = random.uniform(0.01, 0.05)
        cvar_threshold = random.uniform(0.03, 0.08)

        current_var = var_threshold + random.uniform(0.001, 0.02)
        current_cvar = cvar_threshold + random.uniform(0.001, 0.02)

        portfolio_id = uuid.uuid4().hex

        # Настройка мока для возврата случайных данных
        self.mock_analytics.get_tail_risk.return_value = {
            "var": current_var,
            "cvar": current_cvar
        }

        # Выполнение логики
        result = self.trigger.evaluate_hedge_signal(
            portfolio_id=portfolio_id,
            var_limit=var_threshold,
            cvar_limit=cvar_threshold
        )

        # Проверка: сигнал должен быть True, так как метрики превысили порог
        self.assertTrue(result['hedge_required'])
        self.assertEqual(result['portfolio_id'], portfolio_id)
        self.assertGreater(result['coverage_ratio'], 0)

    def test_no_hedge_required_under_threshold(self):
        # Генерируем случайные безопасные значения
        var_threshold = 0.1
        cvar_threshold = 0.15

        current_var = random.uniform(0.01, 0.05)
        current_cvar = random.uniform(0.01, 0.05)

        portfolio_id = uuid.uuid4().hex

        self.mock_analytics.get_tail_risk.return_value = {
            "var": current_var,
            "cvar": current_cvar
        }

        result = self.trigger.evaluate_hedge_signal(
            portfolio_id=portfolio_id,
            var_limit=var_threshold,
            cvar_limit=cvar_threshold
        )

        self.assertFalse(result['hedge_required'])
        self.assertEqual(result['coverage_ratio'], 0.0)

    def test_db_storage_interaction(self):
        # Проверка записи события в БД с рандомными данными
        event_id = uuid.uuid4().hex
        status = random.choice(['ACTIVE', 'INACTIVE', 'PENDING'])

        with patch('skills.market_portfolio_hedge_trigger.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value.hex = event_id

            self.trigger.log_trigger_event(status)

            # Проверяем, что метод БД был вызван с нашими случайными данными
            self.mock_db.save_event.assert_called_once()
            args, _ = self.mock_db.save_event.call_args
            self.assertIn(event_id, args[0].values())
            self.assertIn(status, args[0].values())

    def test_data_stream_processing(self):
        # Имитация чтения потока данных
        random_payload = f"data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_payload)

        with patch('builtins.open', return_value=mock_stream):
            result = self.trigger.process_external_risk_feed('dummy_path')

            # Проверяем, что парсер обработал именно наш случайный байтовый мусор
            self.assertIsNotNone(result)
            self.assertTrue(result.startswith('data_'))

    def test_exception_handling_on_invalid_metrics(self):
        # Проверка поведения при получении некорректных данных
        portfolio_id = uuid.uuid4().hex
        self.mock_analytics.get_tail_risk.side_effect = ValueError("Invalid metrics")

        with self.assertRaises(ValueError):
            self.trigger.evaluate_hedge_signal(
                portfolio_id=portfolio_id,
                var_limit=0.05,
                cvar_limit=0.05
            )

if __name__ == '__main__':
    unittest.main()