import unittest
import uuid
import random
import os
from skills.market_portfolio_risk_profile import evaluate_portfolio_risk_profile
from skills.db_storage import save_risk_assessment, get_risk_assessment
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_portfolio_performance_analytics import calculate_volatility

class TestIntegrationMarketPortfolioRiskProfile(unittest.TestCase):
    def test_evaluate_portfolio_risk_profile_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_count = random.randint(3, 10)
        mock_assets = [f"ASSET_{uuid.uuid4().hex[:4].upper()}" for _ in range(asset_count)]

        collected_data = collect_portfolio_data(portfolio_id, mock_assets)
        self.assertIsNotNone(collected_data)

        volatility_metrics = calculate_volatility(collected_data)
        self.assertIsInstance(volatility_metrics, dict)

        risk_profile_result = evaluate_portfolio_risk_profile(portfolio_id, volatility_metrics)

        self.assertIn("risk_score", risk_profile_result)
        self.assertIn("recommendation", risk_profile_result)
        self.assertEqual(risk_profile_result["portfolio_id"], portfolio_id)

        save_risk_assessment(portfolio_id, risk_profile_result)

        persisted_data = get_risk_assessment(portfolio_id)
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data["portfolio_id"], portfolio_id)
        self.assertEqual(persisted_data["risk_score"], risk_profile_result["risk_score"])

if __name__ == "__main__":
    unittest.main()