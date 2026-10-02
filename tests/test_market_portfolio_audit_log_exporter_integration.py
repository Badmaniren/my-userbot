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
        self.test_id = str(uuid.uuid4())
        self.storage_file = f"test_audit_storage_{self.test_id}.json"
        self.export_json_path = f"test_export_{self.test_id}.json"
        self.export_csv_path = f"test_export_{self.test_id}.csv"
        
        self.random_scenario = f"scenario_{uuid.uuid4()}"
        self.random_loss = round(random.uniform(1000.0, 50000.0), 2)
        self.random_timestamp = random.randint(1600000000, 1700000000)

        self.initial_data = [
            {
                "event_id": self.test_id,
                "stress_scenario": self.random_scenario,
                "estimated_loss": self.random_loss,
                "timestamp": self.random_timestamp
            }
        ]

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.initial_data, f, ensure_ascii=False)

        self.market_parser = MarketParser()
        self.exporter = MarketPortfolioAuditLogExporter(self.storage_file)

    def tearDown(self):
        for file_path in [self.storage_file, self.export_json_path, self.export_csv_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_market_parser_and_exporter_integration(self):
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан в setUp")
        
        is_valid = self.exporter.verify_log_integrity()
        self.assertTrue(is_valid, "Целостность логов должна успешно подтвердиться")

        summary = self.exporter.get_audit_stream_summary()
        self.assertIn("total_records", summary)
        self.assertEqual(summary["total_records"], 1, "Количество записей должно совпадать с добавленной")

        export_json_result = self.exporter.export_aggregated_report(self.export_json_path, format_type="json")
        self.assertTrue(export_json_result, "Экспорт в JSON должен завершиться успешно")
        self.assertTrue(os.path.exists(self.export_json_path), "Экспортированный JSON файл должен существовать")

        with open(self.export_json_path, 'r', encoding='utf-8') as f:
            loaded_json_data = json.load(f)
            self.assertIsInstance(loaded_json_data, list)
            self.assertEqual(len(loaded_json_data), 1)
            self.assertEqual(loaded_json_data[0]["event_id"], self.test_id)
            self.assertEqual(loaded_json_data[0]["stress_scenario"], self.random_scenario)
            self.assertEqual(loaded_json_data[0]["estimated_loss"], self.random_loss)

        export_csv_result = self.exporter.export_aggregated_report(self.export_csv_path, format_type="csv")
        self.assertTrue(export_csv_result, "Экспорт в CSV должен завершиться успешно")
        self.assertTrue(os.path.exists(self.export_csv_path), "Экспортированный CSV файл должен существовать")

        with open(self.export_csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["event_id"], self.test_id)
            self.assertEqual(rows[0]["stress_scenario"], self.random_scenario)
            self.assertEqual(float(rows[0]["estimated_loss"]), self.random_loss)

        adapter_result = self.exporter.generate_audit_log(f"test_adapter_export_{self.test_id}.json")
        self.assertTrue(adapter_result, "Метод адаптера generate_audit_log должен отработать корректно")
        
        adapter_export_file = f"test_adapter_export_{self.test_id}.json"
        if os.path.exists(adapter_export_file):
            os.remove(adapter_export_file)


if __name__ == '__main__':
    unittest.main()