import os
import shutil
import tempfile
import unittest
import uuid
import random

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export,
)


class RealFileStorage:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def save(self, payload):
        record_id = payload.get("audit_id", str(uuid.uuid4()))
        file_path = os.path.join(self.base_dir, f"{record_id}.json")
        market_portfolio_stress_audit_summary_vault_process(file_path, payload)
        return {"status": "saved", "path": file_path, "record_id": record_id}


class RealMarketParser:
    def __init__(self):
        self.stream_parsed = False

    def parse_stream(self):
        self.stream_parsed = True


class RealExtractorTool:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True


class RealStressReporter:
    def __init__(self, audit_id, metrics):
        self.audit_id = audit_id
        self.metrics = metrics

    def generate(self):
        return {
            "audit_id": self.audit_id,
            "metrics": self.metrics,
            "status": "ready"
        }


class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_pipeline_with_real_dependencies(self):
        audit_id = f"audit-{uuid.uuid4()}"
        random_var = round(random.uniform(1000.0, 50000.0), 4)
        random_cvar = round(random_var * random.uniform(1.1, 1.5), 4)
        random_drawdown = round(random.uniform(5.0, 45.0), 2)
        
        metrics = {
            "var_99": random_var,
            "cvar_99": random_cvar,
            "max_drawdown_pct": random_drawdown
        }

        real_db = RealFileStorage(self.test_dir)
        real_parser = RealMarketParser()
        real_extractor = RealExtractorTool()
        real_reporter = RealStressReporter(audit_id, metrics)

        result = start_new(
            db_storage=real_db,
            market_parser=real_parser,
            extractor_tool_1790087207=real_extractor,
            market_portfolio_stress_reporter=real_reporter
        )

        self.assertTrue(real_parser.stream_parsed)
        self.assertTrue(real_extractor.extracted)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"]["audit_id"], audit_id)
        self.assertEqual(result["payload"]["metrics"]["var_99"], random_var)

        expected_filepath = os.path.join(self.test_dir, f"{audit_id}.json")
        self.assertTrue(os.path.exists(expected_filepath))
        self.assertGreater(os.path.getsize(expected_filepath), 0)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(expected_filepath, audit_id)
        self.assertTrue(is_valid)

        wrong_audit_id = f"wrong-{uuid.uuid4()}"
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(expected_filepath, wrong_audit_id)
        self.assertFalse(is_invalid)

        export_result = market_portfolio_stress_audit_summary_vault_export(expected_filepath, format="json")
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], audit_id)
        self.assertEqual(export_result["data"]["metrics"]["cvar_99"], random_cvar)
        self.assertEqual(export_result["data"]["metrics"]["max_drawdown_pct"], random_drawdown)

    def test_storage_vault_lifecycle_isolation(self):
        audit_id = f"vault-test-{uuid.uuid4()}"
        sub_folder = os.path.join(self.test_dir, "nested_vault", str(uuid.uuid4()))
        file_path = os.path.join(sub_folder, f"summary_{audit_id}.json")

        random_score = random.uniform(0.1, 0.99)
        payload = {
            "audit_id": audit_id,
            "stress_index": random_score,
            "tags": [str(uuid.uuid4()), str(uuid.uuid4())]
        }

        process_res = market_portfolio_stress_audit_summary_vault_process(file_path, payload)
        self.assertEqual(process_res["status"], "saved")
        self.assertEqual(process_res["audit_id"], audit_id)
        self.assertTrue(os.path.exists(file_path))

        valid = market_portfolio_stress_audit_summary_vault_validate(file_path, audit_id)
        self.assertTrue(valid)

        exported = market_portfolio_stress_audit_summary_vault_export(file_path)
        self.assertEqual(exported["data"]["stress_index"], random_score)
        self.assertEqual(exported["data"]["tags"], payload["tags"])


if __name__ == "__main__":
    unittest.main()