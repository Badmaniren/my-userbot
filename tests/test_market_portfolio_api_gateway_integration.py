import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway
from skills.db_storage import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_report_generator import MarketReportGenerator

class TestMarketPortfolioAPIGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.url = f"http://example.com/api/{uuid.uuid4()}"
        
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        self.gateway = MarketPortfolioAPIGateway(self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_gateway_export_and_integration(self):
        random_sub_id = str(uuid.uuid4())
        
        summary_data = self.gateway.export_portfolio_summary(self.url)
        self.assertIsInstance(summary_data, dict)
        
        valuation = PortfolioValuation(self.storage_file)
        direct_summary = valuation.get_total_summary(self.url)
        
        report_gen = MarketReportGenerator(self.storage_file)
        report_data = report_gen.generate_symbol_report(self.symbol)
        
        self.assertIsNotNone(summary_data)
        self.assertTrue(os.path.exists(self.storage_file))

if __name__ == "__main__":
    unittest.main()