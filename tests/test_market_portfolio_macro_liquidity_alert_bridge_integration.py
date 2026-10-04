import unittest
import uuid
import random
from skills.market_portfolio_macro_liquidity_alert_bridge import market_portfolio_macro_liquidity_alert_bridge
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.db_storage import db_storage

class TestMarketPortfolioMacroLiquidityAlertBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.bridge = market_portfolio_macro_liquidity_alert_bridge()
        self.portfolio_id = f"test-portfolio-{uuid.uuid4()}"

    def test_process_macro_liquidity_alerts_integration(self):
        result = self.bridge.process_macro_liquidity_alerts(self.portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertIn("alert_dispatched", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)

        if result["alert_dispatched"]:
            self.assertIn("alert_id", result)
            self.assertTrue(uuid.UUID(result["alert_id"]))

    def test_batch_process_portfolios_integration(self):
        portfolio_ids = [f"portfolio-{uuid.uuid4()}" for _ in range(random.randint(2, 4))]
        results = self.bridge.batch_process_portfolios(portfolio_ids)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(portfolio_ids))

        for res, pid in zip(results, portfolio_ids):
            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], pid)

    def test_generate_and_route_alert_integration(self):
        random_alert_id = str(uuid.uuid4())
        random_correlation_id = str(uuid.uuid4())
        payload = {
            "portfolio_id": self.portfolio_id,
            "alert_id": random_alert_id,
            "correlation_id": random_correlation_id
        }

        routed_result = self.bridge.generate_and_route_alert(payload)

        self.assertIsInstance(routed_result, dict)
        self.assertEqual(routed_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(routed_result.get("alert_id"), random_alert_id)
        self.assertEqual(routed_result.get("correlation_id"), random_correlation_id)
        self.assertEqual(routed_result.get("alert_status"), "routed")

if __name__ == "__main__":
    unittest.main()