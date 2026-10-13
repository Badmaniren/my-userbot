import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stress_audit_executive_brief import (
    MarketPortfolioStressAuditExecutiveBrief,
    market_portfolio_stress_audit_executive_brief
)


class TestMarketPortfolioStressAuditExecutiveBrief(unittest.TestCase):

    def test_executive_brief_class_generation_success(self):
        audit_id = uuid.uuid4().hex
        threshold = random.uniform(0.1, 0.9)
        mock_score = random.uniform(20.0, 95.0)

        mock_reporter = unittest.mock.MagicMock()
        mock_reporter.fetch_report.return_value = {"score": mock_score, "risk": "CRITICAL"}

        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.render.return_value = b"binary_image_stream_" + uuid.uuid4().bytes

        mock_db = unittest.mock.MagicMock()

        brief_instance = MarketPortfolioStressAuditExecutiveBrief(
            db_storage=mock_db,
            visualizer=mock_visualizer,
            reporter=mock_reporter
        )

        result = brief_instance.generate_brief(audit_id=audit_id, threshold=threshold)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["audit_id"], audit_id)
        self.assertEqual(result["risk_score"], mock_score)
        self.assertIn("brief_id", result)
        self.assertIn("recommendation", result)
        self.assertIn("recommendations", result)
        self.assertGreater(result["visual_artifact_size"], 0)
        mock_db.save.assert_called_once()

    def test_executive_brief_class_invalid_audit_id(self):
        brief_instance = MarketPortfolioStressAuditExecutiveBrief()
        threshold = random.uniform(0.0, 1.0)
        with self.assertRaises(ValueError):
            brief_instance.generate_brief(audit_id="", threshold=threshold)

    def test_executive_brief_class_without_dependencies(self):
        audit_id = uuid.uuid4().hex
        threshold = random.uniform(0.0, 1.0)
        brief_instance = MarketPortfolioStressAuditExecutiveBrief()

        result = brief_instance.generate_brief(audit_id=audit_id, threshold=threshold)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["audit_id"], audit_id)
        self.assertIsInstance(result["risk_score"], float)
        self.assertIn(result["recommendation"], ["EXECUTE_IMMEDIATE_HEDGE", "HOLD"])

    def test_functional_brief_payload_execution(self):
        portfolio_id = uuid.uuid4().hex
        var_val = random.uniform(50.0, 120.0)
        payload = {
            "portfolio_id": portfolio_id,
            "stress_report": {
                "var_99": var_val
            }
        }

        mock_db_callable = unittest.mock.MagicMock()

        with patch("skills.market_portfolio_stress_audit_executive_brief.db_storage", mock_db_callable):
            result = market_portfolio_stress_audit_executive_brief(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["risk_score"], var_val)
        self.assertIn("brief_id", result)
        self.assertIsInstance(result["recommendations"], list)
        self.assertTrue(len(result["recommendations"]) > 0)
        mock_db_callable.assert_called_once()

    def test_functional_brief_payload_object_db(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "stress_report": {}
        }

        mock_db_obj = unittest.mock.MagicMock()
        del mock_db_obj.__call__

        with patch("skills.market_portfolio_stress_audit_executive_brief.db_storage", mock_db_obj):
            result = market_portfolio_stress_audit_executive_brief(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        mock_db_obj.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()