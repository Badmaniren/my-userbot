import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_hedge_signal_engine import (
    generate_hedge_signal,
    HedgeSignalEngine
)

class TestMarketPortfolioHedgeSignalEngine(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = str(uuid.uuid4())
        self.random_strategy = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_threshold = random.uniform(0.01, 0.99)
        self.engine = HedgeSignalEngine(portfolio_id=self.random_portfolio_id)

    def test_generate_hedge_signal_success(self):
        stress_score = random.uniform(50.0, 100.0)
        var_value = random.uniform(1000.0, 50000.0)

        mock_stress_data = {
            "score": stress_score,
            "portfolio_id": self.random_portfolio_id
        }
        mock_var_data = {
            "var_95": var_value
        }

        with patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_stress_reporter") as mock_reporter, \
             patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_var_liquidity_core") as mock_var_core, \
             patch("skills.market_portfolio_hedge_signal_engine.db_storage") as mock_db:

            mock_reporter.get_latest_report.return_value = mock_stress_data
            mock_var_core.calculate_var.return_value = mock_var_data
            mock_db.save_signal.return_value = True

            result = generate_hedge_signal(self.random_portfolio_id, strategy=self.random_strategy)

            self.assertIsInstance(result, dict)
            self.assertIn("signal_id", result)
            self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
            self.assertEqual(result["strategy"], self.random_strategy)
            self.assertGreater(result["hedge_weight"], 0.0)
            mock_db.save_signal.assert_called_once()

    def test_engine_stress_threshold_exceeded(self):
        random_stress_level = random.uniform(80.0, 150.0)
        random_exposure = random.uniform(10000.0, 999999.0)

        with patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_scenario_simulator") as mock_simulator, \
             patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_valuation") as mock_valuation:

            mock_simulator.run_simulation.return_value = {"max_drawdown": random_stress_level}
            mock_valuation.get_total_exposure.return_value = random_exposure

            signal = self.engine.evaluate_risk_and_trigger(threshold=self.random_threshold)

            self.assertIsNotNone(signal)
            self.assertEqual(signal["portfolio_id"], self.random_portfolio_id)
            self.assertIn("recommended_action", signal)
            self.assertTrue(len(signal["recommended_action"]) > 0)

    def test_engine_stream_processing_with_io(self):
        random_byte_stream = io.BytesIO(uuid.uuid4().bytes + bytes(random.choices(string.ascii_letters.encode(), k=32)))

        with patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_collector_agent") as mock_collector:
            mock_collector.stream_market_data.return_value = random_byte_stream

            processed = self.engine.process_collector_stream()

            self.assertTrue(processed)
            mock_collector.stream_market_data.assert_called_once()

    def test_alert_dispatch_integration(self):
        random_msg = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
        random_event_sink_id = str(uuid.uuid4())

        with patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_alert_dispatcher") as mock_dispatcher, \
             patch("skills.market_portfolio_hedge_signal_engine.market_portfolio_alert_event_sink") as mock_sink:

            mock_sink.register_event.return_value = random_event_sink_id

            status = self.engine.dispatch_alert(random_msg)

            self.assertTrue(status)
            mock_dispatcher.send.assert_called_once()
            args, _ = mock_dispatcher.send.call_args
            self.assertIn(random_msg, str(args))

if __name__ == "__main__":
    unittest.main()