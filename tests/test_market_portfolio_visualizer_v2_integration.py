import unittest
import os
import uuid
import random
from skills.market_portfolio_visualizer_v2 import (
    MarketPortfolioVisualizer,
    generate_visual_report
)
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_parser import MarketParser
from skills.market_report_generator import MarketReportGenerator

class TestMarketPortfolioVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_market_storage_{self.unique_id}.json"
        self.symbol = f"TICK_{self.unique_id.upper()}"
        self.random_price = round(random.uniform(100.0, 2000.0), 2)
        self.url = f"https://example.com/market/{self.symbol.lower()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_visualizer_integration_pipeline(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.random_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Интеграционный сбой: файл хранилища не создан.")

        valuation = PortfolioValuation(self.storage_file)
        valuation_result = valuation.evaluate_portfolio(self.url)
        self.assertIsNotNone(valuation_result)

        report_gen = MarketReportGenerator(self.storage_file)
        symbol_report = report_gen.generate_symbol_report(self.symbol)
        self.assertIsNotNone(symbol_report)

        visualizer = MarketPortfolioVisualizer(self.storage_file)
        visual_chart = visualizer.generate_ascii_chart(self.symbol)
        pnl_text = visualizer.visualize_pnl(self.symbol)

        self.assertIsInstance(visual_chart, str)
        self.assertIsInstance(pnl_text, str)
        
        pipeline_output = generate_visual_visualizer_report = generate_visual_report(self.storage_file, self.symbol)
        self.assertIsNotNone(pipeline_output)

if __name__ == "__main__":
    unittest.main()