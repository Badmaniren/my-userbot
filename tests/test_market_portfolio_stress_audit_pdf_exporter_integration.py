import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_pdf_exporter import (
    market_portfolio_stress_audit_pdf_exporter_run
)
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_store
)
from skills.db_storage import db_storage_connect

class TestMarketPortfolioStressAuditPdfExporterIntegration(unittest.TestCase):
    def test_pdf_exporter_end_to_end_integration(self):
        db_conn = db_storage_connect()
        audit_id = str(uuid.uuid4())
        portfolio_id = f"port_{random.randint(1000, 9999)}"
        stress_loss_value = round(random.uniform(-50000.0, -1000.0), 2)

        vault_payload = {
            "audit_id": audit_id,
            "portfolio_id": portfolio_id,
            "stress_loss": stress_loss_value,
            "status": "COMPLETED"
        }
        vault_result = market_portfolio_stress_audit_summary_vault_store(db_conn, vault_payload)
        self.assertIn("stored", vault_result)

        export_config = {
            "audit_id": audit_id,
            "include_charts": True,
            "format": "PDF"
        }
        export_result = market_portfolio_stress_audit_pdf_exporter_run(db_conn, export_config)

        self.assertIsInstance(export_result, dict)
        self.assertEqual(export_result.get("audit_id"), audit_id)
        self.assertTrue(export_result.get("success"))
        
        pdf_path = export_result.get("file_path")
        self.assertIsNotNone(pdf_path)
        self.assertTrue(os.path.exists(pdf_path))
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    unittest.main()