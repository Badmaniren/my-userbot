import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import io
import tempfile

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.random_audit_id = str(uuid.uuid4())
        self.random_storage_target = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")
        self.random_format = random.choice(["json", "yaml", "xml"])

    def tearDown(self):
        if os.path.exists(self.random_storage_target):
            try:
                os.remove(self.random_storage_target)
            except OSError:
                pass

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_start_new_success_flow(self):
        db_storage_mock = MagicMock()
        random_save_result = uuid.uuid4().hex
        db_storage_mock.save.return_value = random_save_lee = random_save_result

        extractor_mock = MagicMock()
        market_parser_mock = MagicMock()
        stress_reporter_mock = MagicMock()

        random_payload_key = uuid.uuid4().hex
        random_payload_val = uuid.uuid4().hex
        stress_reporter_mock.generate.return_value = {random_payload_key: random_payload_val}

        kwargs = {
            "db_storage": db_storage_mock,
            "extractor_tool_1790087207": extractor_mock,
            "market_parser": market_parser_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        result = start_new(**kwargs)

        extractor_mock.extract.assert_called_once()
        market_parser_mock.parse_stream.assert_called_once()
        stress_reporter_mock.generate.assert_called_once()
        db_storage_mock.save.assert_called_once()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], random_save_result)
        self.assertEqual(result["payload"][random_payload_key], random_payload_val)

    def test_start_new_invalid_payload_type(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        random_invalid_payload = random.randint(1000, 9999)
        stress_reporter_mock.generate.return_value = random_invalid_payload

        kwargs = {
            "db_storage": db_storage_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_market_portfolio_stress_audit_summary_vault_process_invalid_type(self):
        random_non_dict = random.choice([uuid.uuid4().hex, random.randint(1, 100), None])
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.random_storage_target, random_non_dict)

    def test_market_portfolio_stress_audit_summary_vault_process_success(self):
        random_data_key = uuid.uuid4().hex
        random_data_val = uuid.uuid4().hex
        audit_data = {
            "audit_id": self.random_audit_id,
            random_data_key: random_data_val
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.random_storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], self.random_audit_id)
        self.assertTrue(os.path.exists(self.random_storage_target))

        with open(self.random_storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            self.assertEqual(loaded_data.get("audit_id"), self.random_audit_id)
            self.assertEqual(loaded_data.get(random_data_key), random_data_val)

    def test_market_portfolio_stress_audit_summary_vault_validate_nonexistent(self):
        nonexistent_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")
        is_valid = market_portfolio_stress_audit_summary_vault_validate(nonexistent_path, self.random_audit_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_corrupted_json(self):
        with open(self.random_storage_target, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "{bad_json")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.random_storage_target, self.random_audit_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_success(self):
        audit_data = {"audit_id": self.random_audit_id}
        with open(self.random_storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.random_storage_target, self.random_audit_id)
        self.assertTrue(is_valid)

        wrong_audit_id = str(uuid.uuid4())
        is_valid_wrong = market_portfolio_stress_audit_summary_vault_validate(self.random_storage_target, wrong_audit_id)
        self.assertFalse(is_valid_wrong)

    def test_market_portfolio_stress_audit_summary_vault_export_not_found(self):
        nonexistent_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(nonexistent_path, format=self.random_format)

    def test_market_portfolio_stress_audit_summary_vault_export_success(self):
        random_field_key = uuid.uuid4().hex
        random_field_val = uuid.uuid4().hex
        audit_data = {
            "audit_id": self.random_audit_id,
            random_field_key: random_field_val
        }

        with open(self.random_storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        export_result = market_portfolio_stress_audit_summary_vault_export(self.random_storage_target, format=self.random_format)

        self.assertEqual(export_result["format"], self.random_format)
        self.assertEqual(export_result["data"]["audit_id"], self.random_audit_id)
        self.assertEqual(export_result["data"][random_field_key], random_field_val)

    def test_start_new_with_stream_and_extractors(self):
        db_storage_mock = MagicMock()
        extractor_mock_1 = MagicMock()
        extractor_mock_2 = MagicMock()
        
        # Симулируем наличие метода extract
        extractor_mock_1.extract = MagicMock()
        extractor_mock_2.extract = MagicMock()

        market_parser_mock = MagicMock()
        market_parser_mock.parse_stream = MagicMock()

        stress_reporter_mock = MagicMock()
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        stress_reporter_mock.generate.return_value = {random_key: random_val}

        kwargs = {
            "db_storage": db_storage_mock,
            "extractor_tool_1790087207": extractor_mock_1,
            "extractor_tool_1790102839": extractor_mock_2,
            "market_parser": market_parser_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        res = start_new(**kwargs)

        extractor_mock_1.extract.assert_called_once()
        extractor_mock_2.extract.assert_called_once()
        market_parser_mock.parse_stream.assert_called_once()
        self.assertEqual(res["payload"][random_key], random_val)

    def test_start_new_payload_is_none_defaults_to_ok(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        stress_reporter_mock.generate.return_value = None

        kwargs = {
            "db_storage": db_storage_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        res = start_new(**kwargs)
        self.assertEqual(res["payload"], {"status": "ok"})
        db_storage_mock.save.assert_called_once_with({"status": "ok"})