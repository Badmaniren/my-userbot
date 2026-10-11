import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import string
import tempfile
import io

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    start_neos,
    market_portfolio_stress_audit_summary_vault_start,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.storage_target = os.path.join(self.temp_dir.name, self.random_filename)
        self.expected_audit_id = uuid.uuid4().hex

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_new_missing_db_storage(self):
        random_kwargs = {
            "".join(random.choices(string.ascii_lowercase, k=8)): uuid.uuid4().hex
            for _ in range(3)
        }
        with self.assertRaises(ValueError):
            start_new(**random_kwargs)

    def test_start_new_success_flow(self):
        mock_db_storage = MagicMock()
        random_save_result = uuid.uuid4().hex
        mock_db_storage.save.return_value = random_save_result

        mock_extractor = MagicMock()
        mock_market_parser = MagicMock()
        mock_stress_reporter = MagicMock()

        random_payload_key = uuid.uuid4().hex
        random_payload_val = uuid.uuid4().hex
        mock_stress_reporter.generate.return_value = {random_payload_key: random_payload_val}

        kwargs = {
            "db_storage": mock_db_storage,
            uuid.uuid4().hex: mock_extractor,
            "market_parser": mock_market_parser,
            "market_portfolio_stress_reporter": mock_stress_reporter
        }

        result = start_new(**kwargs)

        mock_extractor.extract.assert_called_once()
        mock_market_parser.parse_stream.assert_called_once()
        mock_stress_reporter.generate.assert_called_once()
        mock_db_storage.save.assert_called_once_with({random_payload_key: random_payload_val})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], random_save_result)
        self.assertEqual(result["payload"][random_payload_key], random_payload_val)

    def test_start_new_payload_type_error(self):
        mock_db_storage = MagicMock()
        mock_stress_reporter = MagicMock()
        random_invalid_payload = uuid.uuid4().hex
        mock_stress_reporter.generate.return_value = random_invalid_payload

        kwargs = {
            "db_storage": mock_db_storage,
            "market_portfolio_stress_reporter": mock_stress_reporter
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_aliases_point_to_start_new(self):
        self.assertEqual(start_neos, start_new)
        self.assertEqual(market_portfolio_stress_audit_summary_vault_start, start_new)

    def test_process_audit_data_success(self):
        random_data = {
            "audit_id": self.expected_audit_id,
            uuid.uuid4().hex: random.randint(1, 1000)
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, random_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], self.expected_audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, random_data)

    def test_process_audit_data_type_error(self):
        random_invalid_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, random_invalid_data)

    def test_validate_storage_target_success(self):
        random_data = {
            "audit_id": self.expected_audit_id,
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(random_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.expected_audit_id)
        self.assertTrue(is_valid)

    def test_validate_storage_target_not_found(self):
        non_existent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        is_valid = market_portfolio_stress_audit_summary_vault_validate(non_existent_path, self.expected_audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_corrupted_json(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "{invalid_json")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.expected_audit_id)
        self.assertFalse(is_valid)

    def test_export_storage_target_success(self):
        random_data = {
            "audit_id": self.expected_audit_id,
            uuid.uuid4().hex: random.randint(100, 999)
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(random_data, f)

        random_format = uuid.uuid4().hex[:5]
        export_result = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=random_format)

        self.assertEqual(export_result["format"], random_format)
        self.assertEqual(export_result["data"], random_data)

    def test_export_storage_target_not_found(self):
        non_existent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(non_existent_path)

    def test_process_stream_handling_with_mock_bytes(self):
        random_bytes_content = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_bytes_content)
        
        random_audit_data = {
            "audit_id": self.expected_audit_id,
            "stream_dump": mock_stream.read().decode('utf-8')
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, random_audit_data)
        self.assertEqual(result["audit_id"], self.expected_audit_id)
        self.assertEqual(result["status"], "saved")