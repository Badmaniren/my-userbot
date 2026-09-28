import unittest
from unittest.mock import patch, mock_open
import io
import uuid
import random
import json
from skills.market_portfolio_hedge_risk_report import generate_hedge_risk_report


class TestMarketPortfolioHedgeRiskReport(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.investor_id = str(uuid.uuid4())
        self.search_tag = f"tag_{uuid.uuid4().hex[:8]}"
        self.output_path = f"/tmp/{uuid.uuid4().hex}.json"

    def test_generate_hedge_risk_report_success(self):
        expected_report_id = str(uuid.uuid4())
        with patch("skills.market_portfolio_hedge_risk_report.str", return_value=expected_report_id):
            result = generate_hedge_risk_report(
                portfolio_id=self.portfolio_id,
                investor_id=self.investor_id
            )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("report_id"), expected_report_id)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("investor_id"), self.investor_id)
        self.assertIn("tail_risk_limit", result)
        self.assertIn("hedge_cost", result)

    def test_generate_hedge_risk_report_with_stream_data(self):
        random_tail_risk = round(random.uniform(0.01, 0.4), 4)
        stream_content = f"tail_risk:{random_tail_risk}|tag:{self.search_tag}".encode("utf-8")
        stream_mock = io.BytesIO(stream_content)

        result = generate_hedge_risk_report(
            stream=stream_mock,
            portfolio_id=self.portfolio_id
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("stream_read_status"), "success")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("data_tag"), self.search_tag)

    def test_generate_hedge_risk_report_empty_storage(self):
        result = generate_hedge_risk_report(
            search_tag=self.search_tag,
            portfolio_id=self.portfolio_id
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "empty")
        self.assertIn(self.search_tag, result.get("message", ""))

    def test_generate_hedge_risk_report_with_metrics_and_output(self):
        valuation_metrics = {"valuation_score": random.randint(100, 999)}
        stress_metrics = {"var_99": random.uniform(0.05, 0.2)}

        with patch("builtins.open", mock_open()) as mock_file:
            result = generate_hedge_risk_report(
                portfolio_id=self.portfolio_id,
                investor_id=self.investor_id,
                valuation_metrics=valuation_metrics,
                stress_metrics=stress_metrics,
                output_path=self.output_path
            )
            mock_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("investor_id"), self.investor_id)
        self.assertEqual(result.get("valuation_metrics"), valuation_metrics)
        self.assertEqual(result.get("stress_metrics"), stress_metrics)

    def test_generate_hedge_risk_report_exception_handling(self):
        broken_stream = io.BytesIO()
        broken_stream.read = lambda: (_ for _ in ()).throw(Exception(uuid.uuid4().hex))

        with self.assertRaises(Exception):
            generate_hedge_risk_report(stream=broken_stream)


if __name__ == "__main__":
    unittest.main()