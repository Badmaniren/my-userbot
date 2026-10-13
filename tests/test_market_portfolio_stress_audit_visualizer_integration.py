import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from skills.market_portfolio_stress_recovery_coordinator_bridge import market_portfolio_stress_recovery_coordinator_bridge

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_visualizer_integration_with_recovery_coordinator(self):
        portfolio_id = str(uuid.uuid4())
        adaptive_score = round(random.uniform(10.0, 95.5), 2)
        
        recovery_payload = {
            "portfolio_id": portfolio_id,
            "recovery_target_score": adaptive_score,
            "mode": "automatic"
        }

        recovery_result = market_portfolio_stress_recovery_coordinator_bridge(recovery_payload)

        visualizer_payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "stream_payload": recovery_result
        }

        visualizer = MarketPortfolioStressAuditVisualizer()
        result = visualizer.visualize(visualizer_payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("adaptive_risk_score"), adaptive_score)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertIn("stream_payload", result)
        self.assertEqual(result["stream_payload"], recovery_result)

if __name__ == "__main__":
    unittest.main()