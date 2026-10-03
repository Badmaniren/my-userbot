import json
import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.db_storage import MarketParser
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter


class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_compliance_hub_")
        self.rand_id = str(uuid.uuid4())
        self.storage_file = os.path.join(self.test_dir, f"storage_{self.rand_id}.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization_default_components(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        self.assertIsInstance(hub.db_storage, MarketParser)
        self.assertIsInstance(hub.audit_exporter, PortfolioAuditLogExporter)

    def test_run_compliance_export_creates_file_and_verifies_integrity(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        unique_token = f"audit_export_{uuid.uuid4().hex}"
        export_file = os.path.join(self.test_dir, f"{unique_token}.json")

        result = hub.run_compliance_export(export_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_file))

        with open(export_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(len(content) > 0)

        integrity_res = hub.check_compliance_integrity()
        self.assertIsInstance(integrity_res, bool)
        self.assertTrue(integrity_res)

        summary = hub.fetch_compliance_summary()
        self.assertIsNotNone(summary)

    def test_load_historical_audit_data_auto_creation_and_reading(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        non_existent_file = os.path.join(self.test_dir, f"hist_{uuid.uuid4().hex}.json")

        data = hub.load_historical_audit_data(non_existent_file)
        self.assertTrue(os.path.exists(non_existent_file))
        self.assertIsInstance(data, (list, dict))

        random_records = [
            {"id": str(uuid.uuid4()), "score": random.uniform(10.0, 500.0), "token": uuid.uuid4().hex}
            for _ in range(3)
        ]
        prepopulated_file = os.path.join(self.test_dir, f"prep_{uuid.uuid4().hex}.json")
        with open(prepopulated_file, "w", encoding="utf-8") as f:
            json.dump(random_records, f)

        loaded = hub.load_historical_audit_data(prepopulated_file)
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[0]["id"], random_records[0]["id"])
        self.assertEqual(loaded[1]["token"], random_records[1]["token"])

    def test_process_stream_and_generate_compliance_log(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        stream_payload = [
            {"event_id": str(uuid.uuid4()), "metric_val": random.randint(1, 1000)}
            for _ in range(5)
        ]
        stream_target = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.log")
        process_res = hub.process_audit_stream_data(stream_target, stream_payload)
        self.assertTrue(process_res)

        log_target = os.path.join(self.test_dir, f"gen_log_{uuid.uuid4().hex}.log")
        generate_res = hub.generate_compliance_log(log_target)
        self.assertTrue(generate_res)

    def test_custom_injected_components_and_price_fallback(self):
        custom_db = MarketParser(self.storage_file)
        custom_exporter = PortfolioAuditLogExporter(self.storage_file)
        hub = MarketPortfolioAuditComplianceHub(
            db_storage=custom_db,
            audit_exporter=custom_exporter
        )

        self.assertIs(hub.db_storage, custom_db)
        self.assertIs(hub.audit_exporter, custom_exporter)

        bogus_url = f"https://non-existent-domain-{uuid.uuid4().hex}.local/quote"
        price = hub.audit_fetch_market_price(bogus_url)
        self.assertIsInstance(price, (int, float))

        summary_a = hub.get_audit_stream_summary()
        summary_b = hub.fetch_compliance_summary()
        self.assertEqual(summary_a, summary_b)

        integrity_a = hub.verify_log_integrity()
        integrity_b = hub.check_compliance_integrity()
        self.assertEqual(integrity_a, integrity_b)


if __name__ == "__main__":
    unittest.main()