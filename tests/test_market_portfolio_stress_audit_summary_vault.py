import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_audit_summary_vault import start_neos, market_portfolio_stress_audit_summary_vault_process, market_portfolio_stress_audit_summary_vault_validate, market_portfolio_stress_audit_summary_vault_export

class TestMarketPortfolioStressAuditSummaryVaultStartNew(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]

    def test_start_new_missing_db_storage_raises_value_error(self):
        rand_key = f"key_{self.random_suffix}"
        rand_val = f"val_{self.random_suffix}"
        with self.assertRaises(ValueError):
            start_new(**{rand_key: rand_val})

    def test_start_new_extracts_dependencies(self):
        db_mock = MagicMock()
        save_result_token = f"res_{uuid.uuid4().hex}"
        db_mock.save.return_value = save_result_token

        extractor_mock = MagicMock()
        
        payload_data = {
            f"key_{uuid.uuid4().hex}": random.randint(1, 1000)
        }
        
        reporter_mock = MagicMock()
        reporter_mock.generate.return_value = payload_data

        parser_mock = MagicMock()

        kwargs = {
            "db_storage": db_mock,
            f"extractor_tool_{uuid.uuid4().hex[:6]}": extractor_mock,
            "market_parser": parser_mock,
            "market_portfolio_stress_reporter": reporter_mock
        }

        result = start_new(**kwargs)

        extractor_mock.extract.assert_called_once()
        parser_mock.parse_stream.assert_called_once()
        reporter_mock.generate.assert_called_once()
        db_mock.save.assert_called_once_with(payload_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_result_token)
        self.assertEqual(result["payload"], payload_data)

    def test_start_new_default_payload_when_reporter_none(self):
        db_mock = MagicMock()
        save_result_token = uuid.uuid4().hex
        db_mock.save.return_value = save_result_token

        kwargs = {
            "db_storage": db_mock,
            "market_portfolio_stress_reporter": None
        }

        result = start_new(**kwargs)

        db_mock.save.assert_called_once_with({"status": "ok"})
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_result_token)
        self.assertEqual(result["payload"], {"status": "ok"})

    def test_start_new_invalid_payload_type_raises_type_error(self):
        db_mock = MagicMock()
        reporter_mock = MagicMock()
        invalid_payload = random.choice([
            random.randint(100, 999),
            "".join(random.choices(string.ascii_letters, k=10)),
            [random.randint(1, 5)]
        ])
        reporter_mock.generate.return_value = invalid_payload

        kwargs = {
            "db_storage": db_mock,
            "market_portfolio_stress_reporter": reporter_mock
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_file_operations_process_validate_export(self):
        target_path = f"/tmp/audit_{uuid.uuid4().hex}.json"
        audit_id_val = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id_val,
            f"metric_{uuid.uuid4().hex[:4]}": random.uniform(10.0, 100.0)
        }

        try:
            process_res = market_portfolio_stress_audit_summary_vault_process(target_path, audit_data)
            self.assertEqual(process_res["status"], "saved")
            self.assertEqual(process_res["audit_id"], audit_id_val)

            is_valid = market_portfolio_stress_audit_summary_vault_validate(target_path, audit_id_val)
            self.assertTrue(is_valid)

            invalid_id = uuid.uuid4().hex
            is_invalid = market_portfolio_stress_audit_summary_vault_validate(target_path, invalid_id)
            self.assertFalse(is_invalid)

            export_res = market_portfolio_stress_audit_summary_vault_export(target_path, format="json")
            self.assertEqual(export_res["format"], "json")
            self.assertEqual(export_res["data"], audit_data)

        finally:
            import os
            if os.path.exists(target_path):
                os.remove(target_path)

    def test_validation_corrupted_json(self):
        target_path = f"/tmp/corrupt_{uuid.uuid4().hex}.json"
        audit_id_val = uuid.uuid4().hex
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("invalid_json_content_{}".format(uuid.uuid4().hex))

            is_valid = market_portfolio_stress_audit_summary_vault_validate(target_path, audit_id_val)
            self.assertFalse(is_valid)
        finally:
            import os
            if os.path.exists(target_path):
                os.remove(target_path)