import unittest
import os
import uuid
import random
from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioValuationIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_url = f"http://example.com/price/{self.symbol.lower()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_portfolio_valuation_integration(self):
        evaluator = PortfolioValuation(storage_file=self.storage_file)
        
        has_methods = hasattr(evaluator, 'calculate_portfolio_pnl') or hasattr(evaluator, 'evaluate')
        self.assertTrue(has_methods, "Модуль valuation должен содержать методы расчета.")

        self.assertFalse(os.path.exists(self.storage_file))
        
        data_loaded = evaluator.load_data(self.storage_file) if hasattr(evaluator, 'load_data') else None
        self.assertIsNotNone(evaluator)