import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_collector_agent import (
    MarketParser,
    PortfolioValuation,
    PortfolioDigestManager,
    PortfolioScenarioSimulator,
    StressReporter,
    PortfolioVisualizer,
    run_pipeline,
    start_new
)

class TestMarketPortfolioCollectorAgent(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.shift = round(random.uniform(1.0, 50.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["symbol"], self.symbol)
        self.assertEqual(data[0]["price"], self.price)
        self.assertIn("timestamp", data[0])

    def test_market_parser_corrupted_file_recovery(self):
        garbage_stream = io.BytesIO(b"INVALID_JSON_STREAM_" + uuid.uuid4().bytes)
        with open(self.storage_file, 'wb') as f:
            f.write(garbage_stream.read())

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["symbol"], self.symbol)

    def test_portfolio_valuation(self):
        valuation = PortfolioValuation(self.storage_file)
        result = valuation.get_total_summary(self.url)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("url"), self.url)
        self.assertEqual(result.get("summary"), "ok")

    def test_portfolio_digest_manager(self):
        digest_manager = PortfolioDigestManager(self.storage_file)
        result = digest_manager.compile_digest(self.symbol, self.url)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("url"), self.url)
        self.assertIn(self.symbol, result.get("digest", ""))

    def test_portfolio_scenario_simulator(self):
        simulator = PortfolioScenarioSimulator(self.storage_file)
        result = simulator.simulate_scenario(self.symbol, self.shift)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("shift"), self.shift)
        self.assertEqual(result.get("result"), "simulated")

    def test_stress_reporter(self):
        reporter = StressReporter(self.storage_file)
        data = reporter.get_stream_data()

        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        self.assertIn("stream", data[0])

    def test_portfolio_visualizer(self):
        visualizer = PortfolioVisualizer(self.storage_file)
        report = visualizer.build_text_report(self.symbol)

        self.assertIsInstance(report, str)
        self.assertIn(self.symbol, report)

    def test_run_pipeline_execution(self):
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            stored_data = json.load(f)
        
        self.assertTrue(any(item["symbol"] == self.symbol for item in stored_data))

    def test_start_new_wrapper(self):
        with patch('skills.market_portfolio_collector_agent.run_pipeline') as mock_run:
            mock_run.return_value = True
            
            res = start_new(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.storage_file
            )

if __name__ == '__main__':
    unittest.main()