import os
import json
import uuid
import random
import tempfile
import unittest

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export,
)


class RealDiskAuditStorage:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.stored_ids = []

    def save(self, payload):
        audit_id = payload.get("audit_id", uuid.uuid4().hex)
        file_path = os.path.join(self.base_dir, f"{audit_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        self.stored_ids.append(audit_id)
        return {"file_path": file_path, "stored_id": audit_id}


class RealStressDataGenerator:
    def __init__(self, generated_data):
        self.generated_data = generated_data

    def generate(self):
        return self.generated_data


class RealStreamParser:
    def __init__(self):
        self.stream_parsed = False

    def parse_stream(self):
        self.stream_parsed = True


class RealExtractorTool:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True


class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_validate_and_export_lifecycle(self):
        random_subfolder = uuid.uuid4().hex
        random_file_name = f"audit_{uuid.uuid4().hex}.json"
        target_path = os.path.join(self.base_path, random_subfolder, random_file_name)

        random_audit_id = f"audit-{uuid.uuid4()}"
        random_var_metric = round(random.uniform(0.05, 0.95), 4)
        random_stress_scenario = f"scenario_{uuid.uuid4().hex[:8]}"

        audit_data = {
            "audit_id": random_audit_id,
            "scenario": random_stress_scenario,
            "metrics": {
                "var_99": random_var_metric,
                "iteration": random.randint(100, 10000),
            },
            "verified": True,
        }

        process_result = market_portfolio_stress_audit_summary_vault_process(
            storage_target=target_path,
            audit_data=audit_data,
        )

        self.assertEqual(process_result.get("status"), "saved")
        self.assertEqual(process_result.get("audit_id"), random_audit_id)
        self.assertTrue(os.path.exists(target_path))

        with open(target_path, "r", encoding="utf-8") as f:
            persisted_content = json.load(f)
        self.assertEqual(persisted_content, audit_data)
        self.assertEqual(persisted_content["audit_id"], random_audit_id)
        self.assertEqual(persisted_content["metrics"]["var_99"], random_var_metric)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=target_path,
            expected_audit_id=random_audit_id,
        )
        self.assertTrue(is_valid)

        mismatched_id = f"wrong-audit-{uuid.uuid4()}"
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=target_path,
            expected_audit_id=mismatched_id,
        )
        self.assertFalse(is_invalid)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            storage_target=target_path,
            format="json",
        )
        self.assertEqual(export_result.get("format"), "json")
        self.assertEqual(export_result.get("data"), audit_data)
        self.assertEqual(export_result.get("data")["scenario"], random_stress_scenario)

    def test_start_new_pipeline_execution_and_storage(self):
        storage = RealDiskAuditStorage(base_dir=self.base_path)
        random_audit_id = f"stream-audit-{uuid.uuid4()}"
        random_loss = round(random.uniform(1000.0, 500000.0), 2)

        payload_to_generate = {
            "audit_id": random_audit_id,
            "stress_loss": random_loss,
            "engine": "monte_carlo",
        }

        reporter = RealStressDataGenerator(generated_data=payload_to_generate)
        parser = RealStreamParser()
        extractor = RealExtractorTool()

        result = start_new(
            db_storage=storage,
            market_portfolio_stress_reporter=reporter,
            market_parser=parser,
            extractor_tool_custom=extractor,
        )

        self.assertEqual(result.get("status"), "success")
        self.assertTrue(parser.stream_parsed)
        self.assertTrue(extractor.extracted)

        saved_payload = result.get("payload")
        self.assertEqual(saved_payload.get("audit_id"), random_audit_id)
        self.assertEqual(saved_payload.get("stress_loss"), random_loss)

        save_result = result.get("save_result")
        saved_file_path = save_result.get("file_path")
        self.assertTrue(os.path.exists(saved_file_path))

        with open(saved_file_path, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        self.assertEqual(disk_data["audit_id"], random_audit_id)
        self.assertEqual(disk_data["stress_loss"], random_loss)
        self.assertIn(random_audit_id, storage.stored_ids)

    def test_start_new_requires_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_process_rejects_non_dict_data(self):
        target_path = os.path.join(self.base_path, f"invalid_{uuid.uuid4().hex}.json")
        invalid_data = [uuid.uuid4().hex, random.randint(1, 100)]
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(
                storage_target=target_path,
                audit_data=invalid_data,
            )

    def test_validation_and_export_missing_file(self):
        non_existent_path = os.path.join(self.base_path, f"missing_{uuid.uuid4().hex}.json")

        self.assertFalse(
            market_portfolio_stress_audit_summary_vault_validate(
                storage_target=non_existent_path,
                expected_audit_id=uuid.uuid4().hex,
            )
        )

        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(
                storage_target=non_existent_path,
                format="json",
            )

    def test_validation_corrupted_json(self):
        corrupted_path = os.path.join(self.base_path, f"corrupted_{uuid.uuid4().hex}.json")
        with open(corrupted_path, "w", encoding="utf-8") as f:
            f.write(f"NOT_JSON_DATA_{uuid.uuid4().hex}")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=corrupted_path,
            expected_audit_id=uuid.uuid4().hex,
        )
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()