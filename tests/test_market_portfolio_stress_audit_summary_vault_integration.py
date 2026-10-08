import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealRealDbStorage:
    def __init__(self, target_path):
        self.target_path = target_path

    def save(self, payload):
        dirname = os.path.dirname(self.target_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return {"saved_to": self.target_path, "bytes": len(json.dumps(payload))}

class RealExtractor:
    def __init__(self, name):
        self.name = name
        self.extracted_count = 0

    def extract(self):
        self.extracted_count += 1
        return {"status": "extracted", "source": self.name}

class RealMarketParser:
    def __init__(self, stream_id):
        self.stream_id = stream_id
        self.parsed = False

    def parse_stream(self):
        self.parsed = True
        return {"stream": self.stream_id, "parsed": True}

class RealStressReporter:
    def __init__(self, risk_level):
        self.risk_level = risk_level

    def generate(self):
        return {
            "status": "ok",
            "risk_level": self.risk_level,
            "random_metric": random.randint(100, 999)
        }

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_vault_storage_{uuid.uuid4().hex}"
        self.storage_target = os.path.join(self.test_dir, f"audit_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_start_new_integration_flow(self):
        db_storage = RealRealDbStorage(self.storage_target)
        extractor_1 = RealExtractor("extractor_tool_1790087207")
        extractor_2 = RealExtractor("extractor_tool_1790102839")
        market_parser = RealMarketParser(f"stream_{uuid.uuid4().hex}")
        
        expected_risk = random.choice(["HIGH", "CRITICAL", "MODERATE", "LOW"])
        stress_reporter = RealStressReporter(expected_risk)

        kwargs = {
            "db_storage": db_storage,
            "extractor_tool_1790087207": extractor_1,
            "extractor_tool_1790102839": extractor_2,
            "market_parser": market_parser,
            "market_portfolio_stress_reporter": stress_reporter
        }

        result = start_new(**kwargs)

        self.assertEqual(result["status"], "success")
        self.assertEqual(extractor_1.extracted_count, 1)
        self.assertEqual(extractor_2.extracted_count, 1)
        self.assertTrue(market_parser.parsed)
        self.assertEqual(result["payload"]["risk_level"], expected_risk)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["risk_level"], expected_risk)

    def test_process_validate_export_integration_cycle(self):
        audit_id = f"audit-id-{uuid.uuid4().hex}"
        risk_score = random.uniform(10.0, 99.9)
        audit_data = {
            "audit_id": audit_id,
            "risk_score": risk_score,
            "details": "Integration test payload execution"
        }

        process_res = market_portfolio_stress_audit_summary_vault_process(
            storage_target=self.storage_target,
            audit_data=audit_data
        )

        self.assertEqual(process_res["status"], "saved")
        self.assertEqual(process_res["audit_id"], audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=self.storage_target,
            expected_audit_id=audit_id
        )
        self.assertTrue(is_valid)

        invalid_check = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=self.storage_target,
            expected_audit_id="wrong-audit-id-12345"
        )
        self.assertFalse(invalid_check)

        export_res = market_portfolio_stress_audit_summary_vault_export(
            storage_target=self.storage_target,
            format="json"
        )
        self.assertEqual(export_res["format"], "json")
        self.assertEqual(export_res["data"]["audit_id"], audit_id)
        self.assertEqual(export_res["data"]["risk_score"], risk_score)

    def test_missing_db_storage_raises_error(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_invalid_payload_type_raises_error(self):
        class BadStressReporter:
            def generate(self):
                return "Not a dictionary payload"

        db_storage = RealRealDbStorage(self.storage_target)
        stress_reporter = BadStressReporter()

        with self.assertRaises(TypeError):
            start_new(db_storage=db_storage, market_portfolio_stress_reporter=stress_reporter)

if __name__ == "__main__":
    unittest.main()