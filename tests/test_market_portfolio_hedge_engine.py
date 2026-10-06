import os
import io
import uuid
import random
import unittest
from unittest.mock import patch, MagicMock

from skills.market_portfolio_hedge_engine import (
    MarketPortfolioHedgeEngine,
    market_portfolio_hedge_engine_run
)


class TestMarketPortfolioHedgeEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.engine = MarketPortfolioHedgeEngine()

    def test_calculate_hedge_positions_default(self):
        res = self.engine.calculate_hedge_positions(self.portfolio_id)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("asset"), self.portfolio_id)
        self.assertEqual(res.get("hedge_size"), 100)

    def test_calculate_hedge_positions_with_simulator(self):
        mock_sim = MagicMock()
        rec_size = random.randint(150, 500)
        mock_sim.run_monte_carlo.return_value = {
            self.portfolio_id: {"recommended_hedge_size": rec_size}
        }

        engine = MarketPortfolioHedgeEngine(market_portfolio_scenario_simulator=mock_sim)
        res = engine.calculate_hedge_positions(self.portfolio_id)

        mock_sim.run_monte_carlo.assert_called_once_with(self.portfolio_id)
        self.assertEqual(res.get("hedge_size"), rec_size)
        self.assertEqual(res.get("asset"), self.portfolio_id)

    def test_execute_hedge_default(self):
        payload = {"symbol": self.symbol, "amount": random.randint(10, 1000)}
        res = self.engine.execute_hedge(payload)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "executed")
        self.assertIn("order_id", res)
        self.assertEqual(res.get("symbol"), self.symbol)

    def test_execute_hedge_with_pipeline(self):
        mock_pipe = MagicMock()
        expected_order_id = f"ord_{uuid.uuid4().hex[:8]}"
        mock_pipe.execute_order.return_value = {
            "status": "pipeline_success",
            "order_id": expected_order_id,
            "symbol": self.symbol
        }

        engine = MarketPortfolioHedgeEngine(market_portfolio_execution_pipeline=mock_pipe)
        payload = {"symbol": self.symbol, "volume": random.random()}
        res = engine.execute_hedge(payload)

        mock_pipe.execute_order.assert_called_once()
        self.assertEqual(res.get("status"), "pipeline_success")
        self.assertEqual(res.get("order_id"), expected_order_id)
        self.assertEqual(res.get("symbol"), self.symbol)

    def test_parse_hedge_stream(self):
        vol_val = round(random.uniform(0.1, 0.9), 4)
        stream_content = f"EXTRA_INFO:abc,PORTFOLIO_ID:{self.portfolio_id},VOL:{vol_val},OTHER:xyz"
        stream_mock = io.BytesIO(stream_content.encode('utf-8'))

        res = self.engine.parse_hedge_stream(stream_mock)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(res.get("volatility"), vol_val)

    def test_evaluate_anomaly_trigger_default(self):
        res = self.engine.evaluate_anomaly_trigger(self.symbol)

        self.assertIsInstance(res, dict)
        self.assertTrue(res.get("hedge_triggered"))
        self.assertEqual(res.get("target"), self.symbol)
        self.assertEqual(res.get("score"), 0.95)

    def test_evaluate_anomaly_trigger_with_detector_and_dispatcher(self):
        mock_detector = MagicMock()
        mock_dispatcher = MagicMock()

        anomaly_score = round(random.uniform(0.5, 1.0), 2)
        mock_detector.check_anomaly.return_value = {
            "is_anomaly": True,
            "score": anomaly_score,
            "target": self.symbol
        }

        engine = MarketPortfolioHedgeEngine(
            market_anomaly_detector=mock_detector,
            market_portfolio_alert_dispatcher=mock_dispatcher
        )

        res = engine.evaluate_anomaly_trigger(self.symbol)

        mock_detector.check_anomaly.assert_called_once_with(self.symbol)
        mock_dispatcher.dispatch.assert_called_once_with(self.symbol, anomaly_score)

        self.assertTrue(res.get("hedge_triggered"))
        self.assertEqual(res.get("target"), self.symbol)
        self.assertEqual(res.get("score"), anomaly_score)

    def test_market_portfolio_hedge_engine_run(self):
        balance = round(random.uniform(1000.0, 50000.0), 2)
        volatility = round(random.uniform(0.01, 0.5), 4)
        mc_metrics = {"var_95": random.uniform(-100, -10)}

        res = market_portfolio_hedge_engine_run(
            portfolio_id=self.portfolio_id,
            balance=balance,
            mc_metrics=mc_metrics,
            volatility=volatility
        )

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("hedge_order_id", res)

        log_path = f"logs/hedge_{self.portfolio_id}.log"
        self.assertTrue(os.path.exists(log_path))

        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.portfolio_id, content)
            self.assertIn(str(balance), content)
            self.assertIn(str(volatility), content)

        if os.path.exists(log_path):
            os.remove(log_path)


if __name__ == "__main__":
    unittest.main()