import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_audit_log_exporter import MarketPortfolioAuditLogExporter
from skills.market_parser import MarketParser


class TestMarketPortfolioAuditLogExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.random_str = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.random_str}.json"
        self.export_file = f"test_export_{self.random_str}.json"
        
        self.test_data = [
            {
                "event_id": str(uuid.uuid4()),
                "stress_scenario": f"scenario_{random.randint(1000, 9999)}",
                "impact_value": round(random.uniform(-50.0, 50.0), 2)
            }
        ]
        
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        for file_path in [self.storage_file, self.export_file]:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_integration_export_and_stream_summary(self):
        exporter = MarketPortfolioAuditLogExporter(self.storage_file)
        
        parser = MarketParser()
        self.assertIsNotNone(parser)

        success = exporter.export_audit_logs(self.export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.export_file))

        with open(self.export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        self.assertEqual(len(exported_data), len(self.test_data))
        self.assertEqual(exported_data[0]["event_id"], self.test_data[0]["event_id"])

        summary = exporter.get_audit_stream_summary()
        self.assertIn("total_records", summary)
        self.assertEqual(summary["total_records"], len(self.test_data))

        is_valid = exporter.verify_log_integrity()
        self.assertTrue(is_valid)

        alt_export_file = f"test_alt_export_{str(uuid.uuid4())}.json"
        try:
            res_gen = exporter.generate_audit_log(alt_export_file)
            self.assertTrue(res_gen)
            self.assertTrue(os.path.exists(alt_export_file))
        finally:
            if os.path.exists(alt_export_file):
                os.remove(alt_export_file)


if __name__ == '__main__':
    unittest.main()