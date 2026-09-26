import os
import uuid
import tempfile
import unittest
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub


class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"storage_{uuid.uuid4().hex}.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compliance_export_lifecycle(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        random_suffix = uuid.uuid4().hex
        export_path = os.path.join(self.temp_dir.name, f"export_{random_suffix}.json")

        self.assertFalse(os.path.exists(export_path))
        result = hub.run_compliance_export(export_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        self.assertGreater(os.path.getsize(export_path), 0)

    def test_export_audit_logs_creates_target_file(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        random_suffix = uuid.uuid4().hex
        export_path = os.path.join(self.temp_dir.name, f"audit_{random_suffix}.json")

        result = hub.export_audit_logs(export_path)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        self.assertGreater(os.path.getsize(export_path), 0)

    def test_compliance_integrity_and_summary_consistency(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)

        integrity_res = hub.check_compliance_integrity()
        self.assertIsInstance(integrity_res, bool)

        verify_res = hub.verify_log_integrity()
        self.assertEqual(integrity_res, verify_res)

        summary_res = hub.fetch_compliance_summary()
        direct_summary = hub.get_audit_stream_summary()
        self.assertEqual(summary_res, direct_summary)

    def test_process_audit_stream_data_and_generate_log(self):
        hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)
        stream_id = str(uuid.uuid4())
        stream_path = os.path.join(self.temp_dir.name, f"stream_{stream_id}.log")
        log_path = os.path.join(self.temp_dir.name, f"comp_log_{stream_id}.log")

        stream_payload = {
            "transaction_ref": stream_id,
            "compliance_status": "APPROVED",
        }

        stream_result = hub.process_audit_stream_data(stream_path, stream_payload)
        self.assertTrue(stream_result)

        gen_result = hub.generate_compliance_log(log_path)
        self.assertTrue(gen_result)

    def test_explicit_inter_skill_integration(self):
        db_instance = MarketParser(self.storage_file)
        exporter_instance = PortfolioAuditLogExporter(self.storage_file)

        hub = MarketPortfolioAuditComplianceHub(
            db_storage=db_instance,
            audit_exporter=exporter_instance,
        )

        random_suffix = uuid.uuid4().hex
        custom_export_path = os.path.join(self.temp_dir.name, f"explicit_{random_suffix}.json")

        export_status = hub.run_compliance_export(custom_export_path)
        self.assertTrue(export_status)
        self.assertTrue(os.path.exists(custom_export_path))

        integrity_status = hub.check_compliance_integrity()
        self.assertIsInstance(integrity_status, bool)


if __name__ == "__main__":
    unittest.main()