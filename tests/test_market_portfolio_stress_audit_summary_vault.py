import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)


class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_target = f"temp_test_vault_{self.random_suffix}.json"

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
                os.rmdir(os.path.dirname(self.storage_target))
            except Exception:
                pass
        if os.path.exists(os.path.dirname(self.storage_target) or "."):
            try:
                parent_dir = os.path.dirname(self.storage_target)
                if parent_dir and os.path.exists(parent_dir):
                    os.rmdir(parent_dir)
            except Exception:
                pass

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new()

    def test_start_new_invalid_payload_type(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        
        random_garbage = random.randint(1000, 99999)
        stress_reporter_mock.generate.return_value = random_garbage

        with self.assertRaises(TypeError):
            start_new(db_storage=db_storage_mock, market_portfolio_stress_reporter=stress_reporter_mock)

    def test_start_new_success_flow(self):
        db_storage_mock = MagicMock()
        save_return_val = uuid.uuid4().hex
        db_storage_mock.save.return_value = save_return_val

        market_parser_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        
        expected_payload_key = uuid.uuid4().hex
        expected_payload_val = uuid.uuid4().hex
        stress_reporter_mock.generate.return_value = {expected_payload_key: expected_payload_val}

        extractor_mock = MagicMock()

        result = start_new(
            db_storage=db_storage_mock,
            market_parser=market_parser_mock,
            market_portfolio_stress_reporter=stress_reporter_mock,
            extractor_tool_random=extractor_mock
        )

        extractor_mock.extract.assert_called_once()
        market_parser_mock.parse_stream.assert_called_once()
        stress_reporter_mock.generate.assert_called_once()
        db_storage_mock.save.assert_called_once()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_return_val)
        self.assertEqual(result["payload"][expected_payload_key], expected_payload_val)

    def test_start_new_none_payload_default(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        stress_reporter_mock.generate.return_value = None

        result = start_new(db_storage=db_storage_mock, market_portfolio_stress_reporter=stress_reporter_mock)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], {"status": "ok"})
        db_storage_mock.save.assert_called_once_with({"status": "ok"})

    def test_vault_process_invalid_data_type(self):
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, "not_a_dict")

    def test_vault_process_and_validate_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id,
            "metric": ''.join(random.choices(string.ascii_letters, k=10)),
            "value": random.uniform(1.0, 100.0)
        }

        res = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(res["status"], "saved")
        self.assertEqual(res["audit_id"], audit_id)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, audit_id)
        self.assertTrue(is_valid)

        wrong_audit_id = uuid.uuid4().hex
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_audit_id)
        self.assertFalse(is_invalid)

    def test_vault_validate_file_not_found(self):
        missing_target = f"nonexistent_{uuid.uuid4().hex}.json"
        audit_id = uuid.uuid4().hex
        res = market_portfolio_stress_audit_summary_vault_validate(missing_target, audit_id)
        self.assertFalse(res)

    def test_vault_validate_corrupted_json(self):
        audit_id = uuid.uuid4().hex
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write("{broken_json_content")

        res = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, audit_id)
        self.assertFalse(res)

    def test_vault_export_file_not_found(self):
        missing_target = f"nonexistent_export_{uuid.uuid4().hex}.json"
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(missing_target)

    def test_vault_export_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id,
            "payload_data": uuid.uuid4().hex
        }
        market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        format_type = uuid.uuid4().hex[:5]
        export_res = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=format_type)

        self.assertEqual(export_res["format"], format_type)
        self.assertEqual(export_res["data"]["audit_id"], audit_id)
        self.assertEqual(export_res["data"]["payload_data"], audit_data["payload_data"])