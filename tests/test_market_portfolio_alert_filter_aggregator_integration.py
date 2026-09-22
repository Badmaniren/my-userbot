import unittest
import os
import uuid
import random
from skills.market_portfolio_alert_filter_aggregator import (
    filter_and_aggregate_alerts
)
from skills.market_portfolio_alert_dispatcher import (
    dispatch_portfolio_alerts
)
from skills.market_portfolio_predictive_aggregator import (
    PredictiveAggregator,
    aggregate_market_forecast
)

class TestMarketPortfolioAlertFilterAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"
        self.url = f"https://example.com/api/market/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"TOKEN_{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.severity_level = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.min_threshold = round(random.uniform(1.0, 10.0), 2)
        self.shift = round(random.uniform(-5.0, 5.0), 2)
        self.channels = ["telegram", "webhook"]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_filter_and_aggregate_pipeline(self):
        aggregator_instance = PredictiveAggregator(storage_file=self.storage_file)
        self.assertIsInstance(aggregator_instance, PredictiveAggregator)

        forecast_result = aggregator_instance.build_predictive_forecast(
            symbol=self.symbol,
            url=self.url,
            shift=self.shift
        )
        self.assertIsInstance(forecast_result, dict)

        independent_forecast = aggregate_market_forecast(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            percentage_shift=self.shift
        )
        self.assertIsInstance(independent_forecast, dict)

        filtered_aggregated_output = filter_and_aggregate_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            shift=self.shift,
            channels=self.channels
        )

        self.assertIsNotNone(filtered_aggregated_output)
        self.assertTrue(
            os.path.exists(self.storage_file),
            "Файл хранилища должен быть создан в процессе интеграционного вызова"
        )

if __name__ == "__main__":
    unittest.main()