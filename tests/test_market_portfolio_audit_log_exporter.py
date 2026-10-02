import unittest
from unittest.mock import patch, mock_open
import json
import io
import uuid
import random
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter, MarketPortfolioAuditLogExporter

class TestPortfolioAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.storage_file_path = f"{uuid.uuid4().hex}.json"
        self.export_file_path = f"{uuid.uuid4().hex}.json"
        self.exporter = PortfolioAuditLogExporter(self.storage_file_path)
        self.adapter = MarketPortfolioAuditLogExporter(self.storage_file_path)

    def test_read_storage_success(self):
        random_id = uuid.uuid4().hex
        random_value = random.randint(1000, 99999)
        mock_data = json.dumps([{"id": random_id, "val": random_value}])

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_data)):
                result = self.exporter._read_storage()
                self.assertIsInstance(result, list)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["id"], random_id)
                self.assertEqual(result[0]["val"], random_value)

    def test_read_storage_non_existent_file(self):
        with patch("os.path.exists", return_value=False):
            result = self.exporter._read_storage()
            self.assertEqual(result, [])

    def test_read_storage_empty_file(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="   ")):
                result = self.exporter._read_storage()
                self.assertEqual(result, [])

    def test_read_storage_json_decode_error(self):
        corrupted_data = f"{uuid.uuid4().hex} ::: invalid json"
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=corrupted_data)):
                with self.assertRaises(json.JSONDecodeError):
                    self.exporter._read_storage()

    def test_export_audit_logs_success(self):
        random_msg = uuid.uuid4().hex
        valid_json = json.dumps({"audit_message": random_msg})

        mock_file_read = mock_open(read_data=valid_json)
        mock_file_write = mock_open()

        with patch("builtins.open", side_effect=[mock_file_read.return_value, mock_file_write.return_value]):
            success = self.exporter.export_audit_logs(self.export_file_path)
            self.assertTrue(success)
            mock_file_write().write.assert_called_once_with(valid_json)

    def test_export_audit_logs_invalid_json(self):
        invalid_data = f"INVALID_{uuid.uuid4().hex}"

        with patch("builtins.open", mock_open(read_data=invalid_data)):
            success = self.exporter.export_audit_logs(self.export_file_path)
            self.assertFalse(success)

    def test_get_audit_stream_summary_list(self):
        record_count = random.randint(1, 15)
        records = [{"log_id": uuid.uuid4().hex} for _ in range(record_count)]
        json_data = json.dumps(records)

        with patch("builtins.open", mock_open(read_data=json_data)):
            summary = self.exporter.get_audit_stream_summary()
            self.assertIn("total_records", summary)
            self.assertEqual(summary["total_records"], record_count)

    def test_get_audit_stream_summary_single_object(self):
        single_record = json.dumps({"single_log": uuid.uuid4().hex})

        with patch("builtins.open", mock_open(read_data=single_record)):
            summary = self.exporter.get_audit_stream_summary()
            self.assertEqual(summary["total_records"], 1)

    def test_get_audit_stream_summary_exception(self):
        with patch("builtins.open", side_effect=IOError):
            summary = self.exporter.get_audit_stream_summary()
            self.assertEqual(summary["total_records"], 0)

    def test_verify_log_integrity_valid(self):
        valid_payload = json.dumps({"status": uuid.uuid4().hex, "code": random.randint(200, 500)})

        with patch("builtins.open", mock_open(read_data=valid_payload)):
            is_valid = self.exporter.verify_log_integrity()
            self.assertTrue(is_valid)

    def test_verify_log_integrity_invalid(self):
        broken_payload = f"BROKEN_LOG_{uuid.uuid4().hex}"

        with patch("builtins.open", mock_open(read_data=broken_payload)):
            is_valid = self.exporter.verify_log_integrity()
            self.assertFalse(is_valid)

    def test_market_adapter_methods(self):
        random_target = f"{uuid.uuid4().hex}.csv"
        valid_json = json.dumps({"adapter_test": uuid.uuid4().hex})

        mock_file_read = mock_open(read_data=valid_json)
        mock_file_write = mock_open()

        with patch("builtins.open", side_effect=[mock_file_read.return_value, mock_file_write.return_value]):
            res_gen = self.adapter.generate_audit_log(random_target)
            self.assertTrue(res_gen)

        mock_file_read_2 = mock_open(read_data=valid_json)
        mock_file_write_2 = mock_open()

        with patch("builtins.open", side_effect=[mock_file_read_2.return_value, mock_file_write_2.return_value]):
            res_proc = self.adapter.process_audit_stream(random_target)
            self.assertTrue(res_proc)

if __name__ == "__main__":
    unittest.main()