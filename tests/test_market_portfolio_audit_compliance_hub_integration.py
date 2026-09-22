import unittest
import os
import tempfile
import uuid
import random

from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter


class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"db_{uuid.uuid4()}.json")
        self.export_path = os.path.join(self.test_dir.name, f"audit_export_{uuid.uuid4()}.json")

        self.db_storage = MarketParser(storage_file=self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(storage_file=self.storage_file)

        self.compliance_hub = MarketPortfolioAuditComplianceHub(
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_compliance_hub_integration_workflow(self):
        self.db_storage.fetch_and_store(self.random_symbol, self.random_price)

        summary = self.compliance_hub.get_audit_stream_summary()
        self.assertIsInstance(summary, dict)

        integrity_status = self.compliance_hub.verify_log_integrity()
        self.assertIsInstance(integrity_status, bool)

        export_success = self.compliance_hub.export_audit_logs(self.export_path)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(self.export_path))

        with open(self.export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0)


if __name__ == "__main__":
    unittest.main()