import os
import tempfile
import unittest
import uuid
import json
from skills.anomaly_logger import AnomalyLogger
from skills.patch_rule_engine import PatchRuleEngine, PatchRuleEngineError


class TestPatchRuleEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file_path = os.path.join(self.temp_dir.name, f"anomalies_{uuid.uuid4().hex}.json")
        self.logger = AnomalyLogger(log_path=self.log_file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_evaluate_clean_patch_passes(self):
        rule_id = f"rule_no_eval_{uuid.uuid4().hex[:8]}"
        rules = [
            {
                "id": rule_id,
                "name": "Disallow eval calls",
                "severity": "HIGH",
                "rule_type": "forbidden_pattern",
                "pattern": r"\beval\(",
            }
        ]
        engine = PatchRuleEngine(rules=rules, logger=self.logger)

        safe_token = f"safe_function_{uuid.uuid4().hex}"
        patch_id = f"patch_{uuid.uuid4().hex}"
        patch_content = (
            f"--- a/service.py\n"
            f"+++ b/service.py\n"
            f"@@ -1,3 +1,4 @@\n"
            f"+def {safe_token}():\n"
            f"+    return 42\n"
        )

        result = engine.evaluate_patch(patch_content=patch_content, patch_id=patch_id)

        self.assertEqual(result.get("patch_id"), patch_id)
        self.assertTrue(result.get("is_valid"))
        self.assertEqual(len(result.get("violations", [])), 0)
        self.assertEqual(len(self.logger.get_anomalies()), 0)

    def test_evaluate_forbidden_pattern_logs_anomaly(self):
        rule_id = f"rule_ban_token_{uuid.uuid4().hex[:8]}"
        forbidden_token = f"DANGEROUS_{uuid.uuid4().hex}"
        rules = [
            {
                "id": rule_id,
                "name": "Ban specific toxic token",
                "severity": "CRITICAL",
                "rule_type": "forbidden_pattern",
                "pattern": forbidden_token,
            }
        ]
        engine = PatchRuleEngine(rules=rules, logger=self.logger)

        patch_id = f"patch_{uuid.uuid4().hex}"
        patch_content = (
            f"--- a/config.py\n"
            f"+++ b/config.py\n"
            f"@@ -10,2 +10,3 @@\n"
            f"+SECRET_OVERRIDE = '{forbidden_token}'\n"
        )

        result = engine.evaluate_patch(patch_content=patch_content, patch_id=patch_id)

        self.assertFalse(result.get("is_valid"))
        violations = result.get("violations", [])
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].get("rule_id"), rule_id)
        self.assertEqual(violations[0].get("severity"), "CRITICAL")
        self.assertIn(forbidden_token, violations[0].get("details", ""))

        anomalies = self.logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        logged_anomaly = anomalies[0]
        self.assertEqual(logged_anomaly.get("severity"), "CRITICAL")
        self.assertIn(rule_id, json.dumps(logged_anomaly.get("details", {})))
        self.assertIn(patch_id, json.dumps(logged_anomaly.get("details", {})))

        self.assertTrue(os.path.exists(self.log_file_path))
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            disk_content = f.read()
        self.assertIn(rule_id, disk_content)
        self.assertIn(forbidden_token, disk_content)

    def test_add_rule_dynamically_and_inspect_structure(self):
        engine = PatchRuleEngine(logger=self.logger)

        max_allowed_lines = 3
        rule_id = f"rule_max_lines_{uuid.uuid4().hex[:8]}"
        rule_definition = {
            "id": rule_id,
            "name": "Limit patch added lines",
            "severity": "MEDIUM",
            "rule_type": "max_added_lines",
            "threshold": max_allowed_lines,
        }
        engine.add_rule(rule_definition)

        patch_id = f"patch_oversized_{uuid.uuid4().hex}"
        added_lines = [f"+line_value_{uuid.uuid4().hex}\n" for _ in range(max_allowed_lines + 2)]
        patch_content = "--- a/module.py\n+++ b/module.py\n@@ -0,0 +1,5 @@\n" + "".join(added_lines)

        result = engine.evaluate_patch(patch_content=patch_content, patch_id=patch_id)

        self.assertFalse(result.get("is_valid"))
        violations = result.get("violations", [])
        self.assertTrue(any(v.get("rule_id") == rule_id for v in violations))

        report = self.logger.get_structured_report()
        self.assertIn("total_anomalies", report)
        self.assertGreaterEqual(report["total_anomalies"], 1)

    def test_invalid_rule_schema_raises_engine_error(self):
        engine = PatchRuleEngine(logger=self.logger)
        corrupted_rule = {
            "invalid_field": uuid.uuid4().hex
        }
        with self.assertRaises(PatchRuleEngineError):
            engine.add_rule(corrupted_rule)


if __name__ == "__main__":
    unittest.main()