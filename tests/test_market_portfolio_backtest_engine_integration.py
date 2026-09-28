import unittest
import uuid
import random
import io

from skills.market_portfolio_backtest_engine import MarketPortfolioBacktestEngine, market_portfolio_backtest_engine
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.db_storage import db_storage

class TestMarketPortfolioBacktestEngineIntegration(unittest.TestCase):
    def test_backtest_engine_integration_flow(self):
        strategy_id = f"strat_{uuid.uuid4().hex[:8]}"
        initial_capital = float(random.randint(10000, 1000000))
        historical_data_stream = [
            {"timestamp": i, "price": float(random.randint(100, 200))}
            for i in range(random.randint(3, 10))
        ]

        engine = MarketPortfolioBacktestEngine(
            db_storage=db_storage,
            scenario_simulator=market_portfolio_scenario_simulator,
            slippage_model=market_portfolio_slippage_model
        )

        audit_payload = engine.run_backtest(
            strategy_id=strategy_id,
            historical_data_stream=historical_data_stream,
            initial_capital=initial_capital
        )

        self.assertIsInstance(audit_payload, dict)
        self.assertEqual(audit_payload.get("strategy_id"), strategy_id)
        self.assertEqual(audit_payload.get("initial_capital"), initial_capital)
        self.assertIn("final_metric", audit_payload)
        self.assertIn("token", audit_payload)

        stream = io.BytesIO()
        export_result = engine.export_backtest_report(stream, audit_payload)
        self.assertTrue(export_result)

        stream.seek(0)
        exported_content = stream.read().decode('utf-8')
        self.assertIn(strategy_id, exported_content)
        self.assertIn(str(initial_capital), exported_content)

        sim_payload = {"final_value": initial_capital * 1.15}
        slip_payload = {"slippage_rate": 0.001}

        functional_result = market_portfolio_backtest_engine(
            strategy_id=strategy_id,
            capital=initial_capital,
            simulator_payload=sim_payload,
            slippage_payload=slip_payload
        )

        self.assertIsInstance(functional_result, dict)
        self.assertIn("backtest_id", functional_result)
        self.assertEqual(functional_result.get("strategy_id"), strategy_id)
        self.assertEqual(functional_result.get("final_metric"), sim_payload["final_value"])

if __name__ == "__main__":
    unittest.main()