import unittest
import tempfile
import os
import json
import csv
import uuid
import random
from unittest.mock import patch, mock_open
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter, MarketPortfolioAuditLogExporter


class TestMarketPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.storage_filename = f"{uuid.uuid4().hex}.json"
        self.export_filename = f"{uuid.uuid4().hex}.json"
        self.csv_export_filename = f"{uuid.uuid4().hex}.csv"

    def tearDown(self):
        for fname in [self.storage_filename, self.export_filename, self.csv_export_filename]:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except OSError:
                    pass

    def test_read_storage_empty_and_missing(self):
        non_existent = f"{uuid.uuid4().hex}.json"
        exporter = PortfolioAuditLogExporter(non_existent)
        res = exporter._read_storage()
        self.assertEqual(res, [])

        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            f.write("   \n  ")
        exporter_empty = PortfolioAuditLogExporter(self.storage_filename)
        self.assertEqual(exporter_empty._read_storage(), [])

    def test_read_storage_valid_data(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(1000, 99999)
        test_data = [{rand_key: rand_val}]
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        data = exporter._read_storage()
        self.assertEqual(data, test_data)
        self.assertEqual(data[0][rand_key], rand_val)

    def test_export_audit_logs_success(self):
        rand_field = uuid.uuid4().hex
        rand_value = uuid.uuid4().hex
        test_content = json.dumps([{rand_field: rand_value}])

        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            f.write(test_content)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        success = exporter.export_audit_logs(self.export_filename)
        self.assertTrue(success)

        self.assertTrue(os.path.exists(self.export_filename))
        with open(self.export_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_export_audit_logs_invalid_json(self):
        random_garbage = f"{uuid.uuid4().hex} unclosed json {uuid.uuid4().hex}"
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            f.write(random_garbage)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        success = exporter.export_audit_logs(self.export_filename)
        self.assertFalse(success)

    def test_get_audit_stream_summary(self):
        count = random.randint(1, 10)
        test_data = [{uuid.uuid4().hex: uuid.uuid4().hex} for _ in range(count)]
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        summary = exporter.get_audit_stream_summary()
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary.get("total_records"), count)

    def test_get_audit_stream_summary_single_item(self):
        test_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        summary = exporter.get_audit_stream_summary()
        self.assertEqual(summary.get("total_records"), 1)

    def test_get_audit_stream_summary_error(self):
        exporter = PortfolioAuditLogExporter(f"{uuid.uuid4().hex}.json")
        summary = exporter.get_audit_stream_summary()
        self.assertEqual(summary.get("total_records"), 0)

    def test_verify_log_integrity_valid(self):
        test_data = {uuid.uuid4().hex: random.random()}
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        self.assertTrue(exporter.verify_log_integrity())

    def test_verify_log_integrity_invalid(self):
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            f.write(uuid.uuid4().hex + " { broken json")

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        self.assertFalse(exporter.verify_log_integrity())

    def test_export_aggregated_report_json(self):
        key1 = uuid.uuid4().hex
        val1 = uuid.uuid4().hex
        test_data = [{key1: val1}]
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        success = exporter.export_aggregated_report(self.export_filename, format_type="json")
        self.assertTrue(success)

        with open(self.export_filename, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, test_data)
        self.assertEqual(loaded[0][key1], val1)

    def test_export_aggregated_report_csv(self):
        col1 = f"col_{uuid.uuid4().hex[:6]}"
        col2 = f"col_{uuid.uuid4().hex[:6]}"
        val1 = uuid.uuid4().hex
        val2 = uuid.uuid4().hex
        test_data = [{col1: val1, col2: val2}]

        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        success = exporter.export_aggregated_report(self.csv_export_filename, format_type="csv")
        self.assertTrue(success)

        with open(self.csv_export_filename, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][col1], val1)
        self.assertEqual(rows[0][col2], val2)

    def test_export_aggregated_report_csv_empty_data(self):
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump([], f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        success = exporter.export_aggregated_report(self.csv_export_filename, format_type="csv")
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.csv_export_filename))

    def test_export_aggregated_report_unsupported_format(self):
        test_data = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        exporter = PortfolioAuditLogExporter(self.storage_filename)
        bad_format = uuid.uuid4().hex
        success = exporter.export_aggregated_report(self.export_filename, format_type=bad_format)
        self.assertFalse(success)

    def test_market_portfolio_audit_log_exporter_aliases(self):
        test_content = json.dumps([{uuid.uuid4().hex: uuid.uuid4().hex}])
        with open(self.storage_filename, 'w', encoding='utf-8') as f:
            f.write(test_content)

        adapter = MarketPortfolioAuditLogExporter(self.storage_filename)
        
        export_target_1 = f"{uuid.uuid4().hex}.json"
        res_gen = adapter.generate_audit_log(export_target_1)
        self.assertTrue(res_gen)
        self.assertTrue(os.path.exists(export_target_1))
        if os.path.exists(export_target_1):
            os.remove(export_target_1)

        export_target_2 = f"{uuid.uuid4().hex}.json"
        res_proc = adapter.process_audit_stream(export_target_2)
        self.assertTrue(res_proc)
        self.assertTrue(os.path.exists(export_target_2))
        if os.path.exists(export_target_2):
            os.remove(export_target_2)