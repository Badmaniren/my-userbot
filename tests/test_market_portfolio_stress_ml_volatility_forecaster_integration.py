import unittest
import uuid
import random
from skills.market_portfolio_stress_ml_volatility_forecaster import market_portfolio_stress_ml_volatility_forecaster

try:
    from skills.db_storage import db_storage
except (ImportError, AttributeError):
    db_storage = None

class TestMarketPortfolioStressMlVolatilityForecasterIntegration(unittest.TestCase):
    def test_ml_volatility_forecaster_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        random_volatility = round(random.uniform(0.1, 0.4), 4)
        threshold = round(random.uniform(0.01, 0.1), 2)

        monte_carlo_output = {
            "volatility": random_volatility
        }

        # Вызываем функцию напрямую без моков, используя реальные зависимости
        result = market_portfolio_stress_ml_volatility_forecaster(
            portfolio_id=portfolio_id,
            monte_carlo_output=monte_carlo_output,
            threshold=threshold,
            stream_data=b"test_stream_data_payload"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")

        expected_forecast = random_volatility * (1.0 + threshold)
        self.assertAlmostEqual(result.get("volatility_forecast"), expected_forecast)

        # Проверяем сохранение в реальное хранилище db_storage, если поддерживается
        if db_storage is not None:
            try:
                stored_data = db_storage(action="get", key=f"volatility_forecast_{portfolio_id}")
            except TypeError:
                try:
                    stored_data = db_storage.fetch(portfolio_id)
                except Exception:
                    stored_data = None

            if stored_data is not None:
                if isinstance(stored_data, dict):
                    self.assertEqual(stored_data.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()
