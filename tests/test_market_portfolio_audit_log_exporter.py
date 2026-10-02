import unittest
from unittest.mock import patch
import os
import json
import csv
import uuid
import random
import io
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter, MarketPortfolioAuditLogExporter


class TestPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.export_file = f"test_export_{uuid.uuid4().hex}.json"
        self.csv_export_file = f"test_export_{uuid.uuid4().hex}.csv"
        self.exporter = PortfolioAuditLogExporter(self.storage_file)
        self.market_exporter = MarketPortfolioAuditLogExporter(self.storage_file)

    def tearDown(self):
        for f in [self.storage_file, self.export_file, self.csv_export_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_read_storage_non_existent(self):
        res = self.exporter._read_storage()
        self.assertEqual(res, [])

    def test_read_storage_empty_file(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            f.write("   ")
        res = self.exporter._read_storage()
        self.assertEqual(res, [])

    def test_read_storage_valid_json(self):
        rand_id = uuid.uuid4().hex
        rand_val = random.randint(100, 999)
        data = [{"id": rand_id, "value": rand_val}]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        res = self.exporter._read_storage()
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], rand_id)
        self.assertEqual(res[0]["value"], rand_val)

    def test_read_storage_invalid_json(self):
        rand_garbage = uuid.uuid4().hex
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            f.write(f"invalid_json_{rand_garbage}")
        res = self.exporter._read_storage()
        self.assertEqual(res, [])

    def test_export_audit_logs_non_existent(self):
        res = self.exporter.export_audit_logs(self.export_file)
        self.assertFalse(res)

    def test_export_audit_logs_invalid_json(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            f.write(uuid.uuid4().hex)
        res = self.exporter.export_audit_logs(self.export_file)
        self.assertFalse(res)

    def test_export_audit_logs_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        data = {rand_key: rand_val}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        res = self.exporter.export_audit_logs(self.export_file)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.export_file))

        with open(self.export_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        self.assertEqual(content[rand_key], rand_val)

    def test_get_audit_stream_summary_non_existent(self):
        summary = self.exporter.get_audit_stream_summary()
        self.assertEqual(summary, {"total_records": 0})

    def test_get_audit_stream_summary_valid(self):
        count = random.randint(1, 10)
        data = [{"index": i, "uuid": uuid.uuid4().hex} for i in range(count)]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        summary = self.exporter.get_audit_stream_summary()
        self.assertEqual(summary["total_records"], count)

    def test_get_audit_stream_summary_single_dict(self):
        data = {"uuid": uuid.uuid4().hex}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        summary = self.exporter.get_audit_stream_summary()
        self.assertEqual(summary["total_records"], 1)

    def test_verify_log_integrity_success(self):
        data = {"status": uuid.uuid4().hex}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        self.assertTrue(self.exporter.verify_log_integrity())

    def test_verify_log_integrity_failure(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            f.write(uuid.uuid4().hex)

        self.assertFalse(self.exporter.verify_log_integrity())

    def test_export_aggregated_report_json(self):
        rand_field = uuid.uuid4().hex
        rand_val = random.randint(1000, 9999)
        data = [{rand_field: rand_val}]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        res = self.exporter.export_aggregated_report(self.export_file, format_type="json")
        self.assertTrue(res)

        with open(self.export_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(loaded[0][rand_field], rand_val)

    def test_export_aggregated_report_csv(self):
        rand_field = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        data = [{rand_field: rand_val}]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        res = self.exporter.export_aggregated_report(self.csv_export_file, format_type="csv")
        self.assertTrue(res)

        with open(self.csv_export_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][rand_field], rand_val)

    def test_export_aggregated_report_csv_empty(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

        res = self.exporter.export_aggregated_report(self.csv_export_file, format_type="csv")
        self.assertTrue(res)

    def test_export_aggregated_report_invalid_format(self):
        res = self.exporter.export_aggregated_report(self.export_file, format_type=uuid.uuid4().hex)
        self.assertFalse(res)

    def test_market_adapter_methods(self):
        rand_str = uuid.uuid4().hex
        data = {"token": rand_str}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        res_gen = self.market_exporter.generate_audit_log(self.export_file)
        self.assertTrue(res_gen)

        res_proc = self.market_exporter.process_audit_stream(f"stream_{self.export_file}")
        self.assertTrue(res_proc)
        
        stream_path = f"stream_{self.export_file}"
        if os.path.exists(stream_path):
            os.remove(stream_path)