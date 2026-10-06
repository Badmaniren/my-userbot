import unittest
import os
import uuid
import random
import tempfile
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"db_{uuid.uuid4().hex}.json")
        self.export_path = os.path.join(self.test_dir.name, f"export_{uuid.uuid4().hex}.json")
        self.history_file = os.path.join(self.test_dir.name, f"history_{uuid.uuid4().hex}.json")

        self.db_storage = MarketParser(self.storage_file)
        self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)

        self.hub = MarketPortfolioAuditComplianceHub(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def tearDown(self) -> None:
        self.test_dir.cleanup()

    def test_compliance_export_and_file_creation(self) -> None:
        random_suffix = uuid.uuid4().hex
        dynamic_export_path = os.path.join(self.test_dir.name, f"export_{random_suffix}.json")

        self.assertFalse(os.path.exists(dynamic_export_path))

        result = self.hub.run_compliance_export(dynamic_export_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(dynamic_export_path))

        with open(dynamic_export_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            self.assertTrue(len(content) > 0)

    def test_load_historical_audit_data_creation(self) -> None:
        random_history_name = os.path.join(self.test_dir.name, f"history_{uuid.uuid4().hex}.json")
        self.assertFalse(os.path.exists(random_history_name))

        history_data = self.hub.load_historical_audit_data(random_history_name)

        self.assertTrue(os.path.exists(random_history_name))
        self.assertIsInstance(history_data, list)

    def test_audit_fetch_market_price_behavior(self) -> None:
        random_price = round(random.uniform(10.0, 1000.0), 2)
        random_url = f"https://api.market.test/asset/{uuid.uuid4().hex}"

        price = self.hub.audit_fetch_market_price(random_url)
        self.assertIsInstance(price, float)
        self.assertGreaterEqual(price, 0.0)

    def test_verify_log_integrity_execution(self) -> None:
        integrity_result = self.hub.check_compliance_integrity()
        self.assertIsInstance(integrity_result, bool)

        direct_integrity = self.hub.verify_log_integrity()
        self.assertIsInstance(direct_integrity, bool)

    def test_fetch_compliance_summary_structure(self) -> None:
        summary = self.hub.fetch_compliance_summary()
        self.assertIsInstance(summary, dict)

        direct_summary = self.hub.get_audit_stream_summary()
        self.assertIsInstance(direct_summary, dict)

    def test_process_and_generate_compliance_log(self) -> None:
        random_stream_id = uuid.uuid4().hex
        stream_data = {"stream_id": random_stream_id, "value": random.randint(1, 100)}

        process_res = self.hub.process_audit_stream_data(self.export_path, stream_data)
        self.assertIsInstance(process_res, bool)

        gen_res = self.hub.generate_compliance_log(self.export_path)
        self.assertIsInstance(gen_res, bool)

    def test_export_audit_logs_fallback(self) -> None:
        random_export = os.path.join(self.test_dir.name, f"fallback_{uuid.uuid4().hex}.json")
        res = self.hub.export_audit_logs(random_export)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(random_export))

if __name__ == "__main__":
    unittest.main()