import unittest
import os
import uuid
import random
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway
from skills.market_portfolio_data_exporter import PortfolioDataExporter

class TestMarketPortfolioIntegrationHub(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.url = f"https://example.com/api/market_{self.random_suffix}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.shifts = [random.randint(1, 5), random.randint(6, 10)]
        
        self.hub = MarketPortfolioIntegrationHub(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_composition_and_integration(self):
        self.assertIsInstance(self.hub.api_gateway, MarketPortfolioAPIGateway)
        self.assertIsInstance(self.hub.data_exporter, PortfolioDataExporter)

        export_result = self.hub.process_and_export(
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertIsInstance(export_result, dict)
        self.assertIn("summary", export_result)

    def test_hub_pipeline_execution(self):
        test_price = round(random.uniform(10.0, 500.0), 2)
        
        if hasattr(self.hub, 'run_full_integration_pipeline'):
            res = self.hub.run_full_integration_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                shifts=self.shifts
            )
            self.assertIsNotNone(res)

if __name__ == "__main__":
    unittest.main()