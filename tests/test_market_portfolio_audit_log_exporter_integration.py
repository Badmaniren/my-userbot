import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_audit_log_exporter import MarketPortfolioAuditLogExporter
from skills.market_parser import MarketParser


class TestMarketPortfolioAuditLogExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.run_id = str(uuid.uuid4())
        self.storage_file = f"test_audit_storage_{self.run_id}.json"
        self.export_file = f"test_audit_export_{self.run_id}.json"
        
        self.parser = MarketParser()
        self.exporter = MarketPortfolioAuditLogExporter(self.storage_file)

        self.target_severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.other_severity = "DEBUG" if self.target_severity != "DEBUG" else "FATAL"

        self.random_id_1 = str(uuid.uuid4())
        self.random_id_2 = str(uuid.uuid4())
        
        self.raw_audit_data = [
            {
                "event_id": self.random_id_1,
                "severity": self.target_severity,
                "message": f"Integration audit test message {random.randint(1000, 9999)}"
            },
            {
                "event_id": self.random_id_2,
                "level": self.other_severity,
                "message": f"Integration audit test message {random.randint(1000, 9999)}"
            }
        ]

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.raw_audit_data, f)

    def tearDown(self):
        for path in [self.storage_file, self.export_file]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_integration_export_audit_logs_with_severity_filtering(self):
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must exist before test")
        
        stream_summary = self.exporter.get_audit_stream_summary()
        self.assertEqual(stream_summary.get("total_records"), 2, "Summary must reflect exact total records in storage")

        is_integrity_valid = self.exporter.verify_log_integrity()
        self.assertTrue(is_integrity_valid, "Log integrity check must pass for valid JSON storage")

        export_result = self.exporter.generate_audit_log(self.export_file, severity_level=self.target_severity)
        self.assertTrue(export_result, "generate_audit_log adapter method must return True on success")
        self.assertTrue(os.path.exists(self.export_file), "Export file must be created on disk")

        with open(self.export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)

        self.assertIsInstance(exported_data, list, "Exported structure must remain a list")
        self.assertEqual(len(exported_data), 1, "Only records matching the target severity level must be exported")
        self.assertEqual(exported_data[0].get("event_id"), self.random_id_1, "Exported record must match the randomized target event ID")
        self.assertNotEqual(exported_data[0].get("event_id"), self.random_id_2, "Non-matching severity records must be filtered out")

        market_parse_result = self.parser
        self.assertIsNotNone(market_parse_result, "MarketParser must be instantiated successfully within integration flow")

    def test_integration_process_audit_stream_adapter(self):
        alt_export_file = f"test_alt_export_{self.run_id}.json"
        try:
            result = self.exporter.process_audit_stream(alt_export_file, severity_level=None)
            self.assertTrue(result, "process_audit_stream adapter method must successfully export without severity filter")
            self.assertTrue(os.path.exists(alt_export_file), "Alternative export file must be created")

            with open(alt_export_file, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            self.assertEqual(len(full_data), 2, "Unfiltered export must contain all records")
        finally:
            if os.path.exists(alt_export_file):
                os.remove(alt_export_file)


if __name__ == '__main__':
    unittest.main()