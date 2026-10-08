import unittest
import os
import uuid
import io
from skills.market_portfolio_stress_audit_pdf_report_builder import market_portfolio_stress_audit_pdf_report_builder
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer

class TestMarketPortfolioStressAuditPdfReportBuilderIntegration(unittest.TestCase):
    def test_pdf_report_builder_integration(self):
        portfolio_id = f"audit_test_{uuid.uuid4().hex[:8]}"
        output_path = f"/tmp/stress_report_{portfolio_id}.pdf"

        dynamic_vault_data = {
            "total_risk": float(uuid.uuid4().int % 100),
            "status": "tested"
        }

        dynamic_chart_id = f"chart_{uuid.uuid4().hex[:6]}"

        report_input = {
            "portfolio_id": portfolio_id,
            "vault_data": dynamic_vault_data,
            "visualizer_data": {
                "chart_id": [dynamic_chart_id]
            },
            "output_path": output_path
        }

        try:
            result = market_portfolio_stress_audit_pdf_report_builder(report_input)

            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("report_path"), output_path)

            self.assertTrue(os.path.exists(output_path))

            with open(output_path, "rb") as f:
                content = f.read().decode('utf-8')
                self.assertIn(portfolio_id, content)
                self.assertIn(dynamic_chart_id, content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

if __name__ == "__main__":
    unittest.main()