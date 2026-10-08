import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import string
import tempfile

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)


class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_start_new_success_flow(self):
        db_storage = MagicMock()
        random_save_result = uuid.uuid4().hex
        db_storage.save.return_value = random_save_result

        extractor = MagicMock()
        market_parser = MagicMock()
        stress_reporter = MagicMock()
        
        random_payload_key = uuid.uuid4().hex
        random_payload_val = uuid.uuid4().hex
        stress_reporter.generate.return_value = {random_payload_key: random_payload_val}

        result = start_new(
            db_storage=db_storage,
            extractor_tool=extractor,
            market_parser=market_parser,
            market_portfolio_stress_reporter=stress_reporter
        )

        extractor.extract.assert_called_once()
        market_parser.parse_stream.assert_called_once()
        stress_reporter.generate.assert_called_once()
        db_storage.save.assert_called_once()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], random_save_result)
        self.assertEqual(result["payload"][random_payload_key], random_payload_val)

    def test_start_new_payload_none_defaults_to_ok(self):
        db_storage = MagicMock()
        stress_reporter = MagicMock()
        stress_reporter.generate.return_value = None

        result = start_new(
            db_storage=db_storage,
            market_portfolio_stress_reporter=stress_reporter
        )

        self.assertEqual(result["payload"], {"status": "ok"})
        db_storage.save.assert_called_once_with({"status": "ok"})

    def test_start_new_payload_type_error(self):
        db_storage = MagicMock()
        stress_reporter = MagicMock()
        random_invalid_payload = random.choice([uuid.uuid4().hex, random.randint(1, 100), 99.99])
        stress_reporter.generate.return_value = random_invalid_payload

        with self.assertRaises(TypeError):
            start_new(
                db_storage=db_storage,
                market_portfolio_stress_reporter=stress_reporter
            )

    def test_market_portfolio_stress_audit_summary_vault_process_success(self):
        random_filename = f"{uuid.uuid4().hex}.json"
        storage_target = os.path.join(self.temp_dir.name, uuid.uuid4().hex, random_filename)
        
        random_audit_id = uuid.uuid4().hex
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        audit_data = {
            "audit_id": random_audit_id,
            random_key: random_val
        }

        result = market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(storage_target))

        with open(storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data["audit_id"], random_audit_id)
        self.assertEqual(loaded_data[random_key], random_val)

    def test_market_portfolio_stress_audit_summary_vault_process_type_error(self):
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        invalid_audit_data = random.choice([uuid.uuid4().hex, random.randint(1, 500), [1, 2, 3]])

        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(storage_target, invalid_audit_data)

    def test_market_portfolio_stress_audit_summary_vault_validate_true(self):
        random_audit_id = uuid.uuid4().hex
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        
        audit_data = {"audit_id": random_audit_id}
        with open(storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, random_audit_id)
        self.assertTrue(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_false_mismatch(self):
        random_audit_id = uuid.uuid4().hex
        wrong_audit_id = uuid.uuid4().hex
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        
        audit_data = {"audit_id": random_audit_id}
        with open(storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, wrong_audit_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_not_found(self):
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        random_audit_id = uuid.uuid4().hex

        is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, random_audit_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_corrupted_json(self):
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        random_audit_id = uuid.uuid4().hex

        with open(storage_target, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "{malformed_json")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, random_audit_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_export_success(self):
        random_audit_id = uuid.uuid4().hex
        random_format = uuid.uuid4().hex[:5]
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        
        audit_data = {"audit_id": random_audit_id, uuid.uuid4().hex: uuid.uuid4().hex}
        with open(storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        export_result = market_portfolio_stress_audit_summary_vault_export(storage_target, format=random_format)

        self.assertEqual(export_result["format"], random_format)
        self.assertEqual(export_result["data"], audit_data)

    def test_market_portfolio_stress_audit_summary_vault_export_file_not_found(self):
        storage_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(storage_target)