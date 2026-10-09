import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from skills.market_portfolio_backtest_evaluator_bridge import market_portfolio_backtest_evaluator_bridge
from skills.market_report_generator import market_report_generator


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_end_to_end_stress_audit_visualizer(self):
        portfolio_uuid = str(uuid.uuid4())
        random_score = round(random.uniform(10.0, 95.5), 2)
        random_tail_risk = round(random.uniform(1.1, 9.9), 2)

        backtest_payload = {
            "portfolio_id": portfolio_uuid,
            "evaluation_metric": "sharpe_ratio",
            "score": random_score
        }
        backtest_result = market_portfolio_backtest_evaluator_bridge(backtest_payload)

        report_payload = {
            "report_id": portfolio_uuid,
            "metrics": {"tail_risk": random_tail_risk},
            "format": "detailed"
        }
        report_result = market_report_generator(report_payload)

        self.assertIsNotNone(backtest_result)
        self.assertIsNotNone(report_result)

        visualizer_instance = MarketPortfolioStressAuditVisualizer(
            market_portfolio_backtest_evaluator_bridge=market_portfolio_backtest_evaluator_bridge,
            market_report_generator=market_report_generator
        )

        combined_payload = {
            "portfolio_id": portfolio_uuid,
            "format": "graphical",
            "adaptive_risk_score": random_score,
            "tail_risk_metrics": {"tail_risk": random_tail_risk},
            "stream_payload": {
                "backtest": backtest_result,
                "report": report_result
            }
        }

        visualization_output = visualizer_instance.visualize(combined_payload)

        self.assertIsInstance(visualization_output, dict)
        self.assertEqual(visualization_output.get("portfolio_id"), portfolio_uuid)
        self.assertEqual(visualization_output.get("status"), "success")
        self.assertEqual(visualization_output.get("adaptive_risk_score"), random_score)
        self.assertEqual(visualization_output.get("tail_risk_metrics"), {"tail_risk": random_tail_risk})
        self.assertIn("stream_payload", visualization_output)

        text_payload = {
            "portfolio_id": portfolio_uuid,
            "format": "text_summary",
            "adaptive_risk_score": random_score,
            "export_to_text_report": True
        }
        text_output = visualizer_instance.visualize(text_payload)

        self.assertIsInstance(text_output, str)
        self.assertIn(portfolio_uuid, text_output)
        self.assertIn(str(random_score), text_output)
        self.assertIn("Exported to text report successfully", text_output)


if __name__ == "__main__":
    unittest.main()