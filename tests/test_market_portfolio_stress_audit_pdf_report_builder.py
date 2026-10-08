import unittest
from unittest.mock import MagicMock, patch
import io
import os
import random
import uuid
from skills.market_portfolio_stress_audit_pdf_report_builder import (
    MarketPortfolioStressAuditPdfReportBuilder,
    market_portfolio_stress_audit_pdf_report_builder
)


class TestMarketPortfolioStressAuditPdfReportBuilder(unittest.TestCase):

    def setUp(self):
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.output_stream = io.BytesIO()
        self.mock_vault = MagicMock()
        self.mock_visualizer = MagicMock()

    def test_market_portfolio_stress_audit_pdf_report_builder_success(self):
        summary_key = f"metric_{uuid.uuid4().hex[:6]}"
        summary_val = random.randint(100, 9999)
        chart_name = f"chart_{uuid.uuid4().hex[:6]}"

        self.mock_vault.get_summary.return_value = {summary_key: summary_val}
        self.mock_visualizer.generate_charts.return_value = [chart_name]

        builder = MarketPortfolioStressAuditPdfReportBuilder(
            vault=self.mock_vault,
            visualizer=self.mock_visualizer
        )

        result = builder.build_report(self.audit_id, self.output_stream)

        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"][summary_key], summary_val)
        self.assertEqual(result["charts_count"], 1)

        output_content = self.output_stream.getvalue().decode('utf-8')
        self.assertIn(self.audit_id, output_content)
        self.assertIn(chart_name, output_content)

        self.mock_vault.get_summary.assert_called_once_with(self.audit_id)
        self.mock_visualizer.generate_charts.assert_called_once_with(self.audit_id)

    def test_market_portfolio_stress_audit_pdf_report_builder_empty_audit_id(self):
        builder = MarketPortfolioStressAuditPdfReportBuilder(
            vault=self.mock_vault,
            visualizer=self.mock_visualizer
        )

        with self.assertRaises(ValueError) as ctx:
            builder.build_report("", self.output_stream)

        self.assertIn("Audit ID cannot be empty", str(ctx.exception))
        self.mock_vault.get_summary.assert_not_called()
        self.mock_visualizer.generate_charts.assert_not_called()

    def test_market_portfolio_stress_audit_pdf_report_builder_none_dependencies(self):
        builder = MarketPortfolioStressAuditPdfReportBuilder(vault=None, visualizer=None)

        result = builder.build_report(self.audit_id, self.output_stream)

        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["summary"], {})
        self.assertEqual(result["charts_count"], 0)

        output_content = self.output_stream.getvalue().decode('utf-8')
        self.assertIn(self.audit_id, output_content)

    def test_functional_adapter_market_portfolio_stress_audit_pdf_report_builder(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        vault_key = f"key_{uuid.uuid4().hex[:6]}"
        vault_val = random.uniform(10.0, 999.0)
        chart_id = f"chart_id_{uuid.uuid4().hex[:6]}"
        output_path = f"/tmp/test_report_{uuid.uuid4().hex[:8]}.pdf"

        report_input = {
            "portfolio_id": portfolio_id,
            "vault_data": {vault_key: vault_val},
            "visualizer_data": {"chart_id": chart_id},
            "output_path": output_path
        }

        try:
            res = market_portfolio_stress_audit_pdf_report_builder(report_input)

            self.assertEqual(res["status"], "success")
            self.assertEqual(res["report_path"], output_path)
            self.assertTrue(os.path.exists(output_path))

            with open(output_path, "rb") as f:
                content = f.read().decode('utf-8')
                self.assertIn(portfolio_id, content)
                self.assertIn(chart_id, content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_functional_adapter_missing_portfolio_id(self):
        report_input = {
            "vault_data": {},
            "visualizer_data": {}
        }

        with self.assertRaises(ValueError) as ctx:
            market_portfolio_stress_audit_pdf_report_builder(report_input)

        self.assertIn("Portfolio ID cannot be empty", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()