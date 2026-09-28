import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_backtest_engine import (
    MarketPortfolioBacktestEngine,
    market_portfolio_backtest_engine
)

class TestMarketPortfolioBacktestEngine(unittest.TestCase):

    def setUp(self):
        self.strategy_id = uuid.uuid4().hex
        self.initial_capital = random.uniform(1000.0, 50000.0)
        self.engine = MarketPortfolioBacktestEngine()

    def test_run_backtest_empty_strategy_raises_value_error(self):
        historical_stream = [random.randint(1, 100) for _ in range(3)]
        with self.assertRaises(ValueError):
            self.engine.run_backtest("", historical_stream, self.initial_capital)

    def test_run_backtest_default_random_flow(self):
        historical_stream = [random.randint(10, 100) for _ in range(4)]
        result = self.engine.run_backtest(self.strategy_id, historical_stream, self.initial_capital)
        self.assertIn("strategy_id", result)
        self.assertEqual(result["strategy_id"], self.strategy_id)
        self.assertEqual(result["initial_capital"], self.initial_capital)
        self.assertIn("final_metric", result)
        self.assertIn("token", result)
        self.assertEqual(result["steps_count"], 5)

    def test_run_backtest_with_simulator_and_slippage_and_db(self):
        historical_stream = [random.randint(100, 500) for _ in range(3)]

        mock_simulator = MagicMock()
        sim_val = random.uniform(5000.0, 15000.0)
        mock_simulator.simulate.return_value = [{"step": 1, "value": sim_val}]

        mock_slippage = MagicMock()
        slip_val = random.uniform(10.0, 50.0)
        mock_slippage.calculate.return_value = slip_val

        mock_db = MagicMock()

        engine = MarketPortfolioBacktestEngine(
            db_storage=mock_db,
            scenario_simulator=mock_simulator,
            slippage_model=mock_slippage
        )

        result = engine.run_backtest(self.strategy_id, historical_stream, self.initial_capital)

        mock_simulator.simulate.assert_called_once_with(historical_stream)
        mock_slippage.calculate.assert_called_once_with(sim_val)
        mock_db.save_audit.assert_called_once()
        self.assertEqual(result["final_metric"], sim_val)
        self.assertEqual(result["steps_count"], 1)

    def test_export_backtest_report_invalid_stream_raises_type_error(self):
        data_dict = {
            "strategy_id": self.strategy_id,
            "initial_capital": self.initial_capital
        }
        invalid_stream = object()
        with self.assertRaises(TypeError):
            self.engine.export_backtest_report(invalid_stream, data_dict)

    def test_export_backtest_report_success(self):
        data_dict = {
            "strategy_id": self.strategy_id,
            "initial_capital": self.initial_capital
        }
        stream = io.BytesIO()
        success = self.engine.export_backtest_report(stream, data_dict)
        self.assertTrue(success)

        stream.seek(0)
        content = stream.read().decode('utf-8')
        self.assertIn(self.strategy_id, content)
        self.assertIn(str(self.initial_capital), content)

    def test_functional_market_portfolio_backtest_engine_helper(self):
        sim_final = random.uniform(2000.0, 99999.0)
        simulator_payload = {"final_value": sim_final, "data": uuid.uuid4().hex}
        slippage_payload = {"model": uuid.uuid4().hex, "rate": random.random()}

        with patch("skills.market_portfolio_backtest_engine.db_storage") as mock_db_func:
            res = market_portfolio_backtest_engine(
                self.strategy_id,
                self.initial_capital,
                simulator_payload,
                slippage_payload
            )

            self.assertEqual(res["strategy_id"], self.strategy_id)
            self.assertEqual(res["initial_capital"], self.initial_capital)
            self.assertEqual(res["final_metric"], sim_final)
            self.assertEqual(res["simulator_payload"], simulator_payload)
            self.assertEqual(res["slippage_payload"], slippage_payload)
            mock_db_func.assert_called_once()

    def test_functional_market_portfolio_backtest_engine_no_final_value(self):
        simulator_payload = {"status": uuid.uuid4().hex}
        slippage_payload = {"rate": random.random()}

        with patch("skills.market_portfolio_backtest_engine.db_storage") as mock_db_func:
            res = market_portfolio_backtest_engine(
                self.strategy_id,
                self.initial_capital,
                simulator_payload,
                slippage_payload
            )

            self.assertEqual(res["final_metric"], self.initial_capital)
            mock_db_func.assert_called_once()

if __name__ == "__main__":
    unittest.main()