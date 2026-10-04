import unittest
from unittest.mock import patch
import io
import random
import uuid
import string

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def setUp(self):
        self.random_string = "".join(random.choices(string.ascii_letters, k=10))
        self.db_mock = io.BytesIO(self.random_string.encode('utf-8'))
        self.visualizer_instance = MarketPortfolioStressAuditVisualizer(db_storage=self.db_mock)

    def test_init_and_dependencies(self):
        dep_key = uuid.uuid4().hex
        dep_val = uuid.uuid4().hex
        visualizer = MarketPortfolioStressAuditVisualizer(**{dep_key: dep_val, "db_storage": self.db_mock})
        self.assertEqual(visualizer.dependencies[dep_key], dep_val)
        self.assertEqual(visualizer.db_storage, self.db_mock)

    def test_visualize_wrapper_delegates_correctly(self):
        portfolio_id = uuid.uuid4().hex
        score = random.uniform(1.0, 100.0)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": score
        }
        
        result_direct = market_portfolio_stress_audit_visualizer(payload)
        result_wrapped = self.visualizer_instance.visualize(payload)
        
        self.assertEqual(result_direct, result_wrapped)
        self.assertIn(portfolio_id, result_wrapped)
        self.assertIn(str(score), result_wrapped)

    def test_non_dict_payload_returns_string(self):
        rand_int = random.randint(-10000, 10000)
        payload = f"{self.random_string}_{rand_int}"
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertEqual(result, str(payload))

    def test_text_summary_format_basic(self):
        report_id = uuid.uuid4().hex
        payload = {
            "report_id": report_id,
            "format": "text_summary"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(report_id, result)
        self.assertIn("Portfolio Stress Audit Summary", result)
        self.assertNotIn("Adaptive Risk Score", result)

    def test_text_summary_format_with_adaptive_score_and_export(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = round(random.uniform(0.0, 10.0), 2)
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, result)
        self.assertIn(str(adaptive_score), result)
        self.assertIn("Exported to text report successfully", result)

    def test_graphical_format_basic(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical"
        }
        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertNotIn("adaptive_risk_score", result)
        self.assertNotIn("tail_risk_metrics", result)
        self.assertNotIn("stream_payload", result)

    def test_graphical_format_extended_metrics(self):
        portfolio_id = uuid.uuid4().hex
        adaptive_score = random.randint(100, 999)
        tail_risk_metric_key = uuid.uuid4().hex
        tail_risk_metric_val = random.random()
        stream_val = uuid.uuid4().hex

        payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": {tail_risk_metric_key: tail_risk_metric_val},
            "stream_payload": stream_val
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["adaptive_risk_score"], adaptive_score)
        self.assertEqual(result["tail_risk_metrics"][tail_risk_metric_key], tail_risk_metric_val)
        self.assertEqual(result["stream_payload"], stream_val)

    def test_io_stream_handling_with_mock(self):
        mock_data = io.BytesIO(uuid.uuid4().bytes)
        with patch('skills.market_portfolio_stress_audit_visualizer.requests.get') as mock_requests:
            mock_response = mock_requests.return_value
            mock_response.content = mock_data.read()
            
            portfolio_id = uuid.uuid4().hex
            payload = {
                "portfolio_id": portfolio_id,
                "format": "graphical",
                "stream_payload": mock_response.content.hex()
            }
            result = market_portfolio_stress_audit_visualizer(payload)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["stream_payload"], mock_response.content.hex())


if __name__ == '__main__':
    unittest.main()