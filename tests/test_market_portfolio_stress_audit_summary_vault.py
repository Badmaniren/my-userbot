import os
import sys
import json
import uuid
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import skills.market_portfolio_stress_audit_summary_vault as vault_module


class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def _generate_random_string(self, length=12):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _generate_audit_payload(self):
        audit_id = f"audit_{uuid.uuid4().hex}"
        var_metric = round(random.uniform(0.01, 0.99), 4)
        cvar_metric = round(var_metric + random.uniform(0.01, 0.15), 4)
        scenarios_count = random.randint(5, 50)
        return {
            "audit_id": audit_id,
            "metrics": {
                "var_99": var_metric,
                "cvar_99": cvar_metric,
                "stress_scenarios_evaluated": scenarios_count,
            },
            "status": "completed",
            "token": uuid.uuid4().hex
        }

    def test_start_new_missing_db_storage_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            vault_module.start_new()
        self.assertIn("db_storage is required", str(context.exception))

        with self.assertRaises(ValueError):
            vault_module.start_new(db_storage=None)

    def test_start_new_triggers_extractors_and_parsers(self):
        mock_db = MagicMock()
        save_return_token = uuid.uuid4().hex
        mock_db.save.return_value = {"save_id": save_return_token}

        extractor_1 = MagicMock()
        extractor_2 = MagicMock()
        market_parser = MagicMock()

        custom_key_1 = f"extractor_tool_{uuid.uuid4().hex[:8]}"
        custom_key_2 = f"extractor_tool_{uuid.uuid4().hex[:8]}"

        payload = self._generate_audit_payload()
        stress_reporter = MagicMock()
        stress_reporter.generate.return_value = payload

        kwargs = {
            "db_storage": mock_db,
            custom_key_1: extractor_1,
            custom_key_2: extractor_2,
            "market_parser": market_parser,
            "market_portfolio_stress_reporter": stress_reporter,
        }

        result = vault_module.start_new(**kwargs)

        extractor_1.extract.assert_called_once()
        extractor_2.extract.assert_called_once()
        market_parser.parse_stream.assert_called_once()
        stress_reporter.generate.assert_called_once()

        mock_db.save.assert_called_once_with(payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], {"save_id": save_return_token})
        self.assertEqual(result["payload"], payload)

    def test_start_new_default_payload_when_reporter_missing_or_returns_none(self):
        mock_db = MagicMock()
        save_val = random.randint(1000, 9999)
        mock_db.save.return_value = save_val

        result = vault_module.start_new(db_storage=mock_db)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], {"status": "ok"})
        self.assertEqual(result["save_result"], save_val)
        mock_db.save.assert_called_once_with({"status": "ok"})

    def test_start_new_reporter_returns_invalid_type_raises_type_error(self):
        mock_db = MagicMock()
        stress_reporter = MagicMock()
        invalid_payloads = [
            random.randint(100, 999),
            uuid.uuid4().hex,
            [random.random(), random.random()],
            (uuid.uuid4().hex,)
        ]
        chosen_invalid = random.choice(invalid_payloads)
        stress_reporter.generate.return_value = chosen_invalid

        with self.assertRaises(TypeError) as ctx:
            vault_module.start_new(
                db_storage=mock_db,
                market_portfolio_stress_reporter=stress_reporter
            )
        self.assertIn("payload must be a dictionary", str(ctx.exception))
        mock_db.save.assert_not_called()

    def test_start_new_aliases(self):
        self.assertIs(vault_module.start_neos, vault_module.start_new)
        self.assertIs(
            vault_module.market_portfolio_stress_audit_summary_vault_start,
            vault_module.start_new
        )

    def test_process_saves_file_and_returns_id(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sub_dir = os.path.join(tmp_dir, f"sub_{uuid.uuid4().hex[:6]}")
            file_name = f"summary_{uuid.uuid4().hex}.json"
            target_path = os.path.join(sub_dir, file_name)

            payload = self._generate_audit_payload()
            res = vault_module.market_portfolio_stress_audit_summary_vault_process(target_path, payload)

            self.assertEqual(res["status"], "saved")
            self.assertEqual(res["audit_id"], payload["audit_id"])
            self.assertTrue(os.path.exists(target_path))

            with open(target_path, "r", encoding="utf-8") as f:
                saved_content = json.load(f)

            self.assertEqual(saved_content, payload)

    def test_process_invalid_audit_data_type_raises_type_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = os.path.join(tmp_dir, f"file_{uuid.uuid4().hex}.json")
            invalid_data = [uuid.uuid4().hex, random.randint(1, 100)]

            with self.assertRaises(TypeError):
                vault_module.market_portfolio_stress_audit_summary_vault_process(
                    target_path,
                    random.choice(invalid_data)
                )

    def test_validate_success(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, f"audit_{uuid.uuid4().hex}.json")
            payload = self._generate_audit_payload()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            is_valid = vault_module.market_portfolio_stress_audit_summary_vault_validate(
                file_path,
                payload["audit_id"]
            )
            self.assertTrue(is_valid)

    def test_validate_id_mismatch_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, f"audit_{uuid.uuid4().hex}.json")
            payload = self._generate_audit_payload()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            wrong_id = f"wrong_{uuid.uuid4().hex}"
            is_valid = vault_module.market_portfolio_stress_audit_summary_vault_validate(
                file_path,
                wrong_id
            )
            self.assertFalse(is_valid)

    def test_validate_corrupted_json_or_non_existent_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            non_existent = os.path.join(tmp_dir, f"absent_{uuid.uuid4().hex}.json")
            self.assertFalse(
                vault_module.market_portfolio_stress_audit_summary_vault_validate(
                    non_existent,
                    uuid.uuid4().hex
                )
            )

            corrupt_path = os.path.join(tmp_dir, f"corrupt_{uuid.uuid4().hex}.json")
            random_garbage = f"{{ broken json {self._generate_random_string(20)} "
            with open(corrupt_path, "w", encoding="utf-8") as f:
                f.write(random_garbage)

            self.assertFalse(
                vault_module.market_portfolio_stress_audit_summary_vault_validate(
                    corrupt_path,
                    uuid.uuid4().hex
                )
            )

    def test_validate_json_not_a_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, f"array_{uuid.uuid4().hex}.json")
            random_list = [random.randint(1, 100) for _ in range(5)]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(random_list, f)

            self.assertFalse(
                vault_module.market_portfolio_stress_audit_summary_vault_validate(
                    file_path,
                    uuid.uuid4().hex
                )
            )

    def test_export_success(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, f"export_{uuid.uuid4().hex}.json")
            payload = self._generate_audit_payload()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            custom_format = f"custom_{self._generate_random_string(5)}"
            export_result = vault_module.market_portfolio_stress_audit_summary_vault_export(
                file_path,
                format=custom_format
            )

            self.assertEqual(export_result["format"], custom_format)
            self.assertEqual(export_result["data"], payload)

    def test_export_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = os.path.join(tmp_dir, f"missing_{uuid.uuid4().hex}.json")
            with self.assertRaises(FileNotFoundError):
                vault_module.market_portfolio_stress_audit_summary_vault_export(missing_path)


if __name__ == "__main__":
    unittest.main()