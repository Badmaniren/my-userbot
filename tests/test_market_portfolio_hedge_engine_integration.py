import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_hedge_engine import MarketPortfolioHedgeEngine
from skills.tail_risk_analyzer import TailRiskAnalyzer
from skills.db_storage import DBStorage

class TestMarketPortfolioHedgeEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.instrument = f"INST_{random.randint(1000, 9999)}"
        self.strategy_id = f"strat_{uuid.uuid4().hex[:8]}"

        self.db_storage = DBStorage()
        self.tail_risk_analyzer = TailRiskAnalyzer()

        self.hedge_engine = MarketPortfolioHedgeEngine(
            tail_risk_analyzer=self.tail_risk_analyzer,
            portfolio_id=self.portfolio_id,
            db_storage=self.db_storage
        )

    def test_compute_hedge_delta_integration(self):
        beta = self.hedge_engine._fetch_instrument_beta(self.instrument)
        self.assertEqual(beta, 1.0)

        delta = self.hedge_engine.compute_hedge_delta(self.instrument)
        self.assertIsInstance(delta, (int, float))

    def test_generate_hedge_orders_integration(self):
        order = self.hedge_engine.generate_hedge_orders(self.instrument, self.strategy_id)

        self.assertIsInstance(order, dict)
        self.assertEqual(order['instrument'], self.instrument)
        self.assertEqual(order['portfolio_id'], self.portfolio_id)
        self.assertEqual(order['strategy_tag'], self.strategy_id)
        self.assertIn('required_delta', order)
        self.assertIn('timestamp', order)

    def test_calculate_hedge_volume_integration(self):
        var_val = float(random.randint(500, 2000))
        cvar_val = float(random.randint(2000, 10000))
        correlation_factor = round(random.uniform(0.5, 1.5), 2)

        risk_data = {
            "var_95": var_val,
            "cvar_99": cvar_val
        }

        result = self.hedge_engine.calculate_hedge_volume(
            portfolio_id=self.portfolio_id,
            risk_data=risk_data,
            correlation_factor=correlation_factor
        )

        expected_volume = (var_val + cvar_val) * correlation_factor
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["hedge_volume"], expected_volume)
        self.assertEqual(result["instrument_id"], "DEFAULT_HEDGE_INSTRUMENT")

    def test_write_audit_log_integration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, f"audit_{uuid.uuid4().hex[:6]}.log")
            test_message = f"Integration audit test message {uuid.uuid4().hex}"

            self.hedge_engine.write_audit_log(log_path, test_message)

            self.assertTrue(os.path.exists(log_path))
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn(test_message, content)

    def test_generate_report_integration(self):
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, f"report_{uuid.uuid4().hex[:6]}.json")

            self.hedge_engine.generate_report(run_id, report_path)

            self.assertTrue(os.path.exists(report_path))
            import json
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertEqual(data["run_id"], run_id)
                self.assertEqual(data["status"], "success")
                self.assertIn("timestamp", data)

if __name__ == '__main__':
    unittest.main()