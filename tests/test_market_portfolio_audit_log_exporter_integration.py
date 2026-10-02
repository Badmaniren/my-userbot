import unittest
import os
import json
import csv
import uuid
import random
from skills.market_parser import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter, MarketPortfolioAuditLogExporter


class TestPortfolioAuditLogExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.storage_file = f"test_audit_storage_{self.unique_id}.json"
        self.export_file_json = f"test_export_{self.unique_id}.json"
        self.export_file_csv = f"test_export_{self.unique_id}.csv"
        
        self.market_parser = MarketParser()
        self.exporter = MarketPortfolioAuditLogExporter(self.storage_file)

        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_stress_value = round(random.uniform(-50000.0, -1000.0), 2)
        self.random_risk_score = random.randint(1, 100)

        self.test_data = [
            {
                "event_id": str(uuid.uuid4()),
                "portfolio_id": self.random_portfolio_id,
                "stress_loss": self.random_stress_value,
                "risk_score": self.random_risk_score,
                "compliance_status": "APPROVED"
            },
            {
                "event_id": str(uuid.uuid4()),
                "portfolio_id": f"port_{uuid.uuid4().hex[:8]}",
                "stress_loss": round(random.uniform(-100000.0, -50000.0), 2),
                "risk_score": random.randint(50, 100),
                "compliance_status": "FLAGGED"
            }
        ]

    def tearDown(self):
        for file_path in [self.storage_file, self.export_file_json, self.export_file_csv]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_audit_export_and_compliance_workflow(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f, ensure_ascii=False, indent=4)

        self.assertTrue(os.path.exists(self.storage_file))

        is_integrity_valid = self.exporter.verify_log_integrity()
        self.assertTrue(is_integrity_valid)

        summary = self.exporter.get_audit_stream_summary()
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary.get("total_records"), len(self.test_data))

        export_success = self.exporter.export_aggregated_report(self.export_file_json, format_type="json")
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(self.export_file_json))

        with open(self.export_file_json, 'r', encoding='utf-8') as f:
            loaded_exported_data = json.load(f)
        
        self.assertIsInstance(loaded_exported_data, list)
        self.assertEqual(len(loaded_exported_data), len(self.test_data))
        
        found_random_record = False
        for row in loaded_exported_data:
            if row.get("portfolio_id") == self.random_portfolio_id:
                found_random_record = True
                self.assertEqual(row.get("stress_loss"), self.random_stress_value)
                self.assertEqual(row.get("risk_score"), self.random_risk_score)
        self.assertTrue(found_random_record)

        export_csv_success = self.exporter.export_aggregated_report(self.export_file_csv, format_type="csv")
        self.assertTrue(export_csv_success)
        self.assertTrue(os.path.exists(self.export_file_csv))

        with open(self.export_file_csv, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
        
        self.assertEqual(len(csv_rows), len(self.test_data))

        adapter_export_success = self.exporter.generate_audit_log(self.export_file_json + ".adapt")
        self.assertTrue(adapter_export_success)
        self.assertTrue(os.path.exists(self.export_file_json + ".adapt"))
        
        if os.path.exists(self.export_file_json + ".adapt"):
            os.remove(self.export_file_json + ".adapt")


if __name__ == '__main__':
    unittest.main()