import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_audit_log_exporter import MarketPortfolioAuditLogExporter
from skills.market_parser import MarketParser

class TestMarketPortfolioAuditLogExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.storage_filename = f"test_audit_storage_{self.unique_id}.json"
        self.export_filename = f"test_audit_export_{self.unique_id}.json"
        
        self.parser = MarketParser()
        
        self.test_data = [
            {
                "audit_id": str(uuid.uuid4()),
                "stress_scenario": f"crash_test_{random.randint(1000, 9999)}",
                "portfolio_value_impact": round(random.uniform(-50000.0, -1000.0), 2),
                "passed": random.choice([True, False])
            }
        ]
        
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        for filename in [self.storage_filename, self.export_filename]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError:
                    pass

    def test_integration_audit_log_workflow(self):
        exporter = MarketPortfolioAuditLogExporter(self.storage_filename)
        
        is_valid = exporter.verify_log_integrity()
        self.assertTrue(is_valid, "Целостность исходного лога нарушена")

        summary = exporter.get_audit_stream_summary()
        self.assertIn("total_records", summary)
        self.assertEqual(summary["total_records"], len(self.test_data))

        export_success = exporter.generate_audit_log(self.export_filename)
        self.assertTrue(export_success, "Метод генерации аудита завершился неудачно")
        self.assertTrue(os.path.exists(self.export_filename), "Экспортированный файл не был создан")

        with open(self.export_filename, 'r', encoding='utf-8') as f:
            exported_content = json.load(f)
            self.assertIsInstance(exported_content, list)
            self.assertEqual(len(exported_content), len(self.test_data))
            self.assertEqual(exported_content[0]["audit_id"], self.test_data[0]["audit_id"])

        process_success = exporter.process_audit_stream(self.export_filename)
        self.assertTrue(process_success, "Обработка потока аудита завершилась ошибкой")

if __name__ == '__main__':
    unittest.main()