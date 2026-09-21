import unittest
import os
import json
import uuid
import random
from skills.market_parser import MarketParser
from skills.market_portfolio_advanced_metrics import PortfolioAdvancedMetrics

class TestPortfolioAdvancedMetricsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_env_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_market_parser_and_advanced_metrics(self):
        parser = MarketParser(self.storage_file)

        base_price = round(random.uniform(100.0, 500.0), 2)
        prices_sequence = [base_price]

        for _ in range(10):
            change = random.uniform(-0.05, 0.05)
            base_price = round(base_price * (1 + change), 2)
            prices_sequence.append(base_price)

        for p in prices_sequence:
            parser.fetch_and_store(self.symbol, p)

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан навыком MarketParser")

        metrics_calc = PortfolioAdvancedMetrics(self.storage_file)

        stream_data = metrics_calc.get_metrics_stream_dump()
        self.assertIn(self.symbol, stream_data, "Символ должен присутствовать в дампе данных")
        self.assertEqual(len(stream_data[self.symbol]), len(prices_sequence), "Количество записей цен должно совпадать с сохраненным")

        advanced_metrics = metrics_calc.calculate_advanced_metrics(self.symbol)

        self.assertIn("volatility", advanced_metrics)
        self.assertIn("sharpe_ratio", advanced_metrics)
        self.assertIn("sortino_ratio", advanced_metrics)
        self.assertIn("max_drawdown", advanced_metrics)
        self.assertIn("risk_metric", advanced_metrics)

        self.assertIsInstance(advanced_metrics["volatility"], float)
        self.assertIsInstance(advanced_metrics["max_drawdown"], float)

        risk_profile = metrics_calc.evaluate_risk_profile(self.symbol)

        self.assertIn("risk_level", risk_profile)
        self.assertIn("score", risk_profile)
        self.assertIn(risk_profile["risk_level"], ["LOW", "MEDIUM", "HIGH"])
        self.assertIsInstance(risk_profile["score"], float)

if __name__ == "__main__":
    unittest.main()