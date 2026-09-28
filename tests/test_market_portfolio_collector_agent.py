import unittest
from unittest.mock import patch, mock_open
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
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.org/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat = str(random.randint(100000, 999999))
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def test_market_parser_with_io_mocking(self):
        file_path = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(file_path)
        new_price = round(random.uniform(50.0, 500.0), 2)
        
        initial_data = json.dumps([
            {
                "symbol": self.random_symbol,
                "price": self.random_price,
                "timestamp": "2023-01-01T00:00:00"
            }
        ])

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=initial_data)) as mock_file:

            parser.fetch_and_store(self.random_symbol, new_price)
            mock_file.assert_called()

    def test_market_parser_file_not_exists(self):
        file_path = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(file_path)
        new_price = round(random.uniform(1.0, 100.0), 2)

        with patch("os.path.exists", return_value=False), \
             patch("builtins.open", mock_open()) as mock_file:

            parser.fetch_and_store(self.random_symbol, new_price)
            mock_file.assert_called()

    def test_market_parser_with_file_object_stream(self):
        stream_mock = io.BytesIO()
        parser = MarketParser(stream_mock)
        new_price = round(random.uniform(10.0, 99.9), 2)

        with patch("os.path.exists", return_value=False):
            parser.fetch_and_store(self.random_symbol, new_price)
            stream_mock.seek(0)
            content = stream_mock.read().decode('utf-8')
            parsed = json.loads(content)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["symbol"], self.random_symbol)
            self.assertEqual(parsed[0]["price"], new_price)

    def test_portfolio_valuation(self):
        valuation = PortfolioValuation(self.random_storage)
        res = valuation.get_total_summary(self.random_url)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("url"), self.random_url)
        self.assertEqual(res.get("summary"), "ok")

    def test_portfolio_digest_manager(self):
        manager = PortfolioDigestManager(self.random_storage)
        res = manager.compile_digest(self.random_symbol, self.random_url)
        self.assertIsInstance(res, dict)
        self.assertIn(self.random_symbol, res.get("digest", ""))
        self.assertEqual(res.get("url"), self.random_url)

    def test_portfolio_scenario_simulator(self):
        simulator = PortfolioScenarioSimulator(self.random_storage)
        shift = round(random.uniform(-20.0, 20.0), 2)
        res = simulator.simulate_scenario(self.random_symbol, shift)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("symbol"), self.random_symbol)
        self.assertEqual(res.get("shift"), shift)
        self.assertEqual(res.get("result"), "simulated")

    def test_stress_reporter(self):
        reporter = StressReporter(self.random_storage)
        data = reporter.get_stream_data()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_portfolio_visualizer(self):
        visualizer = PortfolioVisualizer(self.random_storage)
        report = visualizer.build_text_report(self.random_symbol)
        self.assertIsInstance(report, str)
        self.assertIn(self.random_symbol, report)

    def test_run_pipeline_flow(self):
        with patch("os.path.exists", return_value=False), \
             patch("skills.market_portfolio_collector_agent.MarketParser.fetch_and_store") as mock_fetch, \
             patch("skills.market_portfolio_collector_agent.PortfolioValuation.get_total_summary") as mock_val, \
             patch("skills.market_portfolio_collector_agent.PortfolioDigestManager.compile_digest") as mock_dig, \
             patch("skills.market_portfolio_collector_agent.PortfolioScenarioSimulator.simulate_scenario") as mock_sim, \
             patch("skills.market_portfolio_collector_agent.StressReporter.get_stream_data") as mock_stress, \
             patch("skills.market_portfolio_collector_agent.PortfolioVisualizer.build_text_report") as mock_vis:

            result = run_pipeline(
                self.random_symbol,
                self.random_url,
                self.random_token,
                self.random_chat,
                self.random_storage
            )

            self.assertTrue(result)
            mock_fetch.assert_called_once()
            mock_val.assert_called_once_with(self.random_url)
            mock_dig.assert_called_once_with(self.random_symbol, self.random_url)
            mock_sim.assert_called_once()
            mock_stress.assert_called_once()
            mock_vis.assert_called_once_with(self.random_symbol)

    def test_start_new_wrapper(self):
        with patch("skills.market_portfolio_collector_agent.run_pipeline", return_value=True) as mock_pipeline:
            res = start_new(
                self.random_symbol,
                self.random_url,
                self.random_token,
                self.random_chat,
                self.random_storage
            )
            self.assertTrue(res)
            mock_pipeline.assert_called_once_with(
                self.random_symbol,
                self.random_url,
                self.random_token,
                self.random_chat,
                self.random_storage
            )