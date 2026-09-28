import unittest
from unittest.mock import patch
import uuid
import random
import io
import os

from skills.market_portfolio_stress_monte_carlo import start_new, run_monte_carlo_stress_test


class TestMarketPortfolioStressMonteCarloArchitect(unittest.TestCase):

    def test_start_new_success_monte_carlo(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        iterations = random.randint(100, 5000)
        res = start_new(portfolio_id=portfolio_id, iterations=iterations)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["iterations_run"], iterations)
        self.assertIn("var", res)
        self.assertIn("cvar", res)

    def test_start_new_failure_handling(self):
        with self.assertRaises(RuntimeError) as ctx:
            start_new(db_storage=None, market_parser=random.choice(["active", "inactive"]))
        self.assertIn("CRITICAL_FAILURE_MOCK", str(ctx.exception))

    def test_start_new_with_anomaly_injection(self):
        anomaly_token = f"anomaly_{uuid.uuid4().hex}"
        volatility_val = round(random.uniform(0.1, 0.9), 4)
        res = start_new(anomaly_signature=anomaly_token, volatility=volatility_val)
        self.assertIsNotNone(res)
        self.assertEqual(res["anomaly_processed"], anomaly_token)
        self.assertEqual(res["volatility_used"], volatility_val)
        self.assertEqual(res["stream_read"], "DATA_STREAM_MOCK")
        self.assertIsInstance(res["stress_score"], int)

    def test_start_new_with_random_audit_export(self):
        dest_path = f"reports/audit_{uuid.uuid4().hex}.json"
        fmt = random.choice(["json", "csv", "xml"])
        res = start_new(format=fmt, destination=dest_path)
        self.assertIsNotNone(res)
        self.assertTrue(res["exported"])
        self.assertEqual(res["path"], dest_path)
        self.assertEqual(res["type"], fmt)

    def test_start_new_edge_case_empty_parameters(self):
        random_hash = f"sentinel_{uuid.uuid4().hex}"
        res = start_new(market_portfolio_autonomous_sentinel=random_hash)
        self.assertIsNotNone(res)
        self.assertEqual(res["sentinel_ack"], random_hash)
        self.assertEqual(res["status"], "idle")

    def test_run_monte_carlo_stress_test_integration(self):
        portfolio_id = f"pid_{uuid.uuid4().hex}"
        capital = round(random.uniform(10000.0, 1000000.0), 2)
        iterations = random.randint(500, 2000)
        volatility = round(random.uniform(0.05, 0.5), 4)
        anomalies = [f"anom_{uuid.uuid4().hex}" for _ in range(random.randint(1, 5))]
        slippage = round(random.uniform(0.001, 0.05), 4)

        res = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            capital=capital,
            iterations=iterations,
            volatility=volatility,
            anomalies=anomalies,
            slippage=slippage
        )

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["initial_capital"], capital)
        self.assertEqual(res["iterations"], iterations)
        self.assertEqual(res["volatility"], volatility)
        self.assertEqual(res["anomalies_count"], len(anomalies))
        self.assertEqual(res["slippage_rate"], slippage)
        self.assertIn("simulation_id", res)
        self.assertIn("var_95", res)
        self.assertIn("report_path", res)
        self.assertTrue(os.path.exists(res["report_path"]))

        if os.path.exists(res["report_path"]):
            try:
                os.remove(res["report_path"])
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()