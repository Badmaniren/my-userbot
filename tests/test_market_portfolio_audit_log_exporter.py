import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json
import os

from skills.market_portfolio_audit_log_exporter import (
    PortfolioAuditLogExporter
)

class TestMarketPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.random_storage_file = f"{uuid.uuid4().hex}.json"
        self.random_export_path = f"{uuid.uuid4().hex}_audit.log"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.random_timestamp = uuid.uuid4().hex

    def tearDown(self):
        for fpath in [self.random_storage_file, self.random_export_path]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def test_exporter_initialization(self):
        exporter = PortfolioAuditLogExporter(self.random_storage_file)
        self.assertEqual(exporter.storage_file, self.random_storage_file)

    def test_export_audit_logs_success(self):
        mock_data = json.dumps([
            {"symbol": self.random_symbol, "price": self.random_price, "event": uuid.uuid4().hex}
        ])

        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_data)) as mock_file:
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            result = exporter.export_audit_logs(self.random_export_path)

            self.assertTrue(result)
            mock_file.assert_any_call(self.random_storage_file, 'r', encoding='utf-8')
            mock_file.assert_any_call(self.random_export_path, 'w', encoding='utf-8')

    def test_export_audit_logs_empty_storage(self):
        with patch("builtins.open", unittest.mock.mock_open(read_data="[]")) as mock_file:
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            result = exporter.export_audit_logs(self.random_export_path)
            self.assertTrue(result)

    def test_export_audit_logs_io_exception(self):
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            result = exporter.export_audit_logs(self.random_export_path)
            self.assertFalse(result)

    def test_get_audit_stream_summary(self):
        event_id = uuid.uuid4().hex
        mock_data = json.dumps([
            {"symbol": self.random_symbol, "price": self.random_price, "event_id": event_id}
        ])

        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_data)):
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            summary = exporter.get_audit_stream_summary()

            self.assertIsInstance(summary, dict)
            self.assertIn("total_records", summary)
            self.assertEqual(summary["total_records"], 1)

    def test_stream_log_export_malformed_json(self):
        corrupted_data = "{" + uuid.uuid4().hex + ": " + uuid.uuid4().hex + "}}"
        with patch("builtins.open", unittest.mock.mock_open(read_data=corrupted_data)):
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            result = exporter.export_audit_logs(self.random_export_path)
            self.assertFalse(result)

    def test_verify_log_integrity(self):
        record_hash = uuid.uuid4().hex
        mock_data = json.dumps([
            {"symbol": self.random_symbol, "hash": record_hash}
        ])

        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_data)):
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            integrity = exporter.verify_log_integrity()
            self.assertIsInstance(integrity, bool)

    def test_stream_binary_io_handling(self):
        binary_garbage = bytes(random.getrandbits(8) for _ in range(64))
        mock_stream = io.BytesIO(binary_garbage)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=mock_stream):
            exporter = PortfolioAuditLogExporter(self.random_storage_file)
            summary = exporter.get_audit_stream_summary()
            self.assertIsInstance(summary, dict)

if __name__ == '__main__':
    unittest.main()