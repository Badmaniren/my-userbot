import unittest
from unittest.mock import patch, mock_open
import json
import os
import random
import uuid
import string
import io
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter, MarketPortfolioAuditLogExporter


class TestMarketPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.export_path = f"{uuid.uuid4().hex}_export.json"
        self.exporter = PortfolioAuditLogExporter(self.storage_file)
        self.adapter = MarketPortfolioAuditLogExporter(self.storage_file)

    def tearDown(self):
        for f in [self.storage_file, self.export_path]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def test_read_storage_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        data = [{random_key: random_val}]

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(data))):
            res = self.exporter._read_storage()
            self.assertEqual(res, data)

    def test_read_storage_not_exists(self):
        with patch("os.path.exists", return_value=False):
            res = self.exporter._read_storage()
            self.assertEqual(res, [])

    def test_read_storage_empty_content(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="   \n")):
            res = self.exporter._read_storage()
            self.assertEqual(res, [])

    def test_read_storage_decode_error(self):
        bad_data = "".join(random.choices(string.ascii_letters, k=10))
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=bad_data)):
            with self.assertRaises((json.JSONDecodeError, ValueError)):
                self.exporter._read_storage()

    def test_export_audit_logs_filtered_severity(self):
        sev1 = uuid.uuid4().hex
        sev2 = uuid.uuid4().hex
        id1 = uuid.uuid4().hex
        id2 = uuid.uuid4().hex

        records = [
            {"id": id1, "severity": sev1},
            {"id": id2, "level": sev2}
        ]

        mock_file = mock_open(read_data=json.dumps(records))
        with patch("builtins.open", mock_file):
            result = self.exporter.export_audit_logs(self.export_path, severity_level=sev1)
            self.assertTrue(result)

    def test_export_audit_logs_dict_data(self):
        sev = uuid.uuid4().hex
        record = {"severity": sev, "data": uuid.uuid4().hex}

        mock_file = mock_open(read_data=json.dumps(record))
        with patch("builtins.open", mock_file):
            result = self.exporter.export_audit_logs(self.export_path, severity_level=uuid.uuid4().hex)
            self.assertTrue(result)

    def test_export_audit_logs_exception(self):
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            result = self.exporter.export_audit_logs(self.export_path)
            self.assertFalse(result)

    def test_get_audit_stream_summary_list(self):
        count = random.randint(1, 10)
        records = [{"id": uuid.uuid4().hex} for _ in range(count)]

        with patch("builtins.open", mock_open(read_data=json.dumps(records))):
            summary = self.exporter.get_audit_stream_summary()
            self.assertEqual(summary.get("total_records"), count)

    def test_get_audit_stream_summary_single(self):
        record = {"id": uuid.uuid4().hex}
        with patch("builtins.open", mock_open(read_data=json.dumps(record))):
            summary = self.exporter.get_audit_stream_summary()
            self.assertEqual(summary.get("total_records"), 1)

    def test_get_audit_stream_summary_error(self):
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            summary = self.exporter.get_audit_stream_summary()
            self.assertEqual(summary.get("total_records"), 0)

    def test_verify_log_integrity_valid(self):
        data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch("builtins.open", mock_open(read_data=json.dumps(data))):
            self.assertTrue(self.exporter.verify_log_integrity())

    def test_verify_log_integrity_invalid(self):
        with patch("builtins.open", mock_open(read_data="{invalid_json")):
            self.assertFalse(self.exporter.verify_log_integrity())

    def test_adapter_generate_audit_log(self):
        sev = uuid.uuid4().hex
        records = [{"severity": sev}]
        with patch("builtins.open", mock_open(read_data=json.dumps(records))):
            res = self.adapter.generate_audit_log(self.export_path, severity_level=sev)
            self.assertTrue(res)

    def test_adapter_process_audit_stream(self):
        sev = uuid.uuid4().hex
        records = [{"level": sev}]
        with patch("builtins.open", mock_open(read_data=json.dumps(records))):
            res = self.adapter.process_audit_stream(self.export_path, severity_level=sev)
            self.assertTrue(res)