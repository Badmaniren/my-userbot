import unittest
import os
import json
import uuid
import random
from datetime import datetime
from skills.market_portfolio_collector_agent import start_new, MarketParser, PortfolioValuation, PortfolioDigestManager, PortfolioScenarioSimulator, StressReporter, PortfolioVisualizer

class TestMarketPortfolioCollectorAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://example.com/api/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_pipeline_integration_real_flow(self):
        random_price = round(random.uniform(10.0, 1500.0), 2)
        
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, random_price)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file was not created by MarketParser")

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)

        self.assertIsInstance(stored_data, list)
        self.assertEqual(len(stored_data), 1)
        self.assertEqual(stored_data[0]["symbol"], self.symbol)
        self.assertEqual(stored_data[0]["price"], random_price)
        self.assertIn("timestamp", stored_data[0])

        success = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertTrue(success, "Pipeline execution failed")

        valuation = PortfolioValuation(self.storage_file)
        summary = valuation.get_total_summary(self.url)
        self.assertEqual(summary.get("url"), self.url)

        digest_manager = PortfolioDigestManager(self.storage_file)
        digest = digest_manager.compile_digest(self.symbol, self.url)
        self.assertIn(self.symbol, digest.get("digest", ""))
        self.assertEqual(digest.get("url"), self.url)

        random_shift = round(random.uniform(-20.0, 20.0), 2)
        simulator = PortfolioScenarioSimulator(self.storage_file)
        sim_result = simulator.simulate_scenario(self.symbol, random_shift)
        self.assertEqual(sim_result.get("symbol"), self.symbol)
        self.assertEqual(sim_result.get("shift"), random_shift)

        stress_reporter = StressReporter(self.storage_file)
        stream_data = stress_reporter.get_stream_data()
        self.assertIsInstance(stream_data, list)
        self.assertTrue(len(stream_data) > 0)

        visualizer = PortfolioVisualizer(self.storage_file)
        report = visualizer.build_text_report(self.symbol)
        self.assertIn(self.symbol, report)

if __name__ == '__main__':
    unittest.main()