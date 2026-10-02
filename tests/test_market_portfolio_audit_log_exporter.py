import unittest
from unittest.mock import patch, mock_open
import json
import os
import uuid
import random
import io

from skills.market_portfolio_audit_log_exporter import (
    PortfolioAuditLogExporter,
    MarketPortfolioAuditLogExporter
)


class TestPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.export_path = f"{uuid.uuid4().hex}.json"
        self.csv_export_path = f"{uuid.uuid4().hex}.csv"
        self.exporter = PortfolioAuditLogExporter(storage_file=self.storage_file)

    def test_read_storage_non_existent(self):
        non_existent_file = f"{uuid.uuid4().hex}.json"
        exporter = PortfolioAuditLogExporter(storage_file=non_existent_file)
        
        with patch('os.path.exists', return_value=False):
            result = exporter._read_storage()
            self.assertEqual(result, [])

    def test_read_storage_empty_content(self):
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="   \n")):
            result = self.exporter._read_storage()
            self.assertEqual(result, [])

    def test_read_storage_valid_json(self):
        random_id = uuid.uuid4().hex
        random_value = random.randint(1000, 9999)
        mock_data = json.dumps([{"id": random_id, "value": random_value}])

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_data)):
            result = self.exporter._read_storage()
            self.assertIsInstance(result, list)
            self.assertEqual(result[0]["id"], random_id)
            self.assertEqual(result[0]["value"], random_value)

    def test_export_audit_logs_success(self):
        random_key = uuid.uuid4().hex
        random_metric = random.uniform(1.0, 100.0)
        valid_json = json.dumps({"key": random_key, "metric": random_metric})

        mock_file = mock_open(read_data=valid_json)
        with patch('builtins.open', mock_file):
            result = self.exporter.export_audit_logs(self.export_path)
            self.assertTrue(result)
            mock_file.assert_any_call(self.export_path, 'w', encoding='utf-8')

    def test_export_audit_logs_invalid_json(self):
        random_garbage = f"{uuid.uuid4().hex} unclosed json {"
        mock_file = mock_open(read_data=random_garbage)
        with patch('builtins.open', mock_file):
            result = self.exporter.export_audit_logs(self.export_path)
            self.assertFalse(result)

    def test_get_audit_stream_summary_list(self):
        count = random.randint(1, 10)
        data = [{"index": i, "uid": uuid.uuid4().hex} for i in range(count)]
        valid_json = json.dumps(data)

        with patch('builtins.open', mock_open(read_data=valid_json)):
            summary = self.exporter.get_audit_stream_summary()
            self.assertIsInstance(summary, dict)
            self.assertEqual(summary.get("total_records"), count)

    def test_get_audit_stream_summary_single_dict(self):
        data = {"uid": uuid.uuid4().hex}
        valid_json = json.dumps(data)

        with patch('builtins.open', mock_open(read_data=valid_json)):
            summary = self.exporter.get_audit_stream_summary()
            self.assertIsInstance(summary, dict)
            self.assertEqual(summary.get("total_records"), 1)

    def test_get_audit_stream_summary_exception(self):
        with patch('builtins.open', side_effect=Exception(uuid.uuid4().hex)):
            summary = self.exporter.get_audit_stream_summary()
            self.assertEqual(summary.get("total_records"), 0)

    def test_verify_log_integrity_true(self):
        valid_json = json.dumps({"status": uuid.uuid4().hex})
        with patch('builtins.open', mock_open(read_data=valid_json)):
            result = self.exporter.verify_log_integrity()
            self.assertTrue(result)

    def test_verify_log_integrity_false(self):
        invalid_json = f"{uuid.uuid4().hex} invalid"
        with patch('builtins.open', mock_open(read_data=invalid_json)):
            result = self.exporter.verify_log_integrity()
            self.assertFalse(result)


class TestMarketPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.export_path = f"{uuid.uuid4().hex}.json"
        self.adapter = MarketPortfolioAuditLogExporter(storage_file=self.storage_file)

    def test_generate_audit_log_delegation(self):
        random_tag = uuid.uuid4().hex
        valid_json = json.dumps({"tag": random_tag})

        with patch('builtins.open', mock_open(read_data=valid_json)):
            result = self.adapter.generate_audit_log(self.export_path)
            self.assertTrue(result)

    def test_process_audit_stream_delegation(self):
        random_tag = uuid.uuid4().hex
        valid_json = json.dumps({"tag": random_tag})

        with patch('builtins.open', mock_open(read_data=valid_json)):
            result = self.adapter.process_audit_stream(self.export_path)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()