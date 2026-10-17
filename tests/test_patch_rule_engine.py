import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.patch_rule_engine import (
    PatchRuleEngine,
    PatchRuleEngineError,
    RuleViolationError
)

class TestPatchRuleEngine(unittest.TestCase):
    def setUp(self):
        self.engine_name = uuid.uuid4().hex
        self.max_retries = random.randint(1, 10)
        self.engine = PatchRuleEngine(name=self.engine_name, retries=self.max_retries)

    def test_initialization_success(self):
        random_id = uuid.uuid4().hex
        custom_threshold = random.random()
        engine = PatchRuleEngine(name=random_id, threshold=custom_threshold)

        self.assertEqual(engine.name, random_id)
        self.assertEqual(engine.threshold, custom_threshold)
        self.assertEqual(len(engine.rules), 0)

    def test_add_rule_and_validate(self):
        rule_id = uuid.uuid4().hex
        rule_pattern = ''.join(random.choices(string.ascii_letters, k=8))

        self.engine.add_rule(rule_id=rule_id, pattern=rule_pattern, severity="ERROR")

        rules = self.engine.get_rules()
        self.assertIn(rule_id, rules)
        self.assertEqual(rules[rule_id]["pattern"], rule_pattern)

        valid_patch_content = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        result = self.engine.validate_patch(valid_patch_content)
        self.assertTrue(result)

    def test_validate_patch_raises_violation(self):
        rule_id = uuid.uuid4().hex
        forbidden_word = uuid.uuid4().hex[:6]

        self.engine.add_rule(rule_id=rule_id, pattern=forbidden_word, severity="CRITICAL")

        malicious_patch = f"def some_func():\n    # {forbidden_word}\n    pass"

        with self.assertRaises(RuleViolationError) as ctx:
            self.engine.validate_patch(malicious_patch)

        self.assertIn(rule_id, str(ctx.exception))

    def test_load_rules_from_stream(self):
        stream_content = f"RULE_{uuid.uuid4().hex}:pattern_{uuid.uuid4().hex[:4]}".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        with patch('skills.patch_rule_engine.open', return_value=mock_stream, create=True):
            random_filepath = f"/var/tmp/{uuid.uuid4().hex}.conf"
            loaded_count = self.engine.load_rules_from_file(random_filepath)

            self.assertGreaterEqual(loaded_count, 1)
            self.assertGreater(len(self.engine.get_rules()), 0)

    def test_engine_error_propagation(self):
        invalid_rule_id = ""
        with self.assertRaises(PatchRuleEngineError):
            self.engine.add_rule(rule_id=invalid_rule_id, pattern=None, severity="UNKNOWN")

    def test_clear_rules(self):
        for _ in range(random.randint(3, 7)):
            self.engine.add_rule(
                rule_id=uuid.uuid4().hex,
                pattern=uuid.uuid4().hex,
                severity="WARNING"
            )

        self.assertGreater(len(self.engine.get_rules()), 0)
        self.engine.clear_rules()
        self.assertEqual(len(self.engine.get_rules()), 0)

    def test_evaluate_telemetry_snapshot(self):
        metric_name = uuid.uuid4().hex
        metric_value = random.randint(100, 9999)

        snapshot = {
            metric_name: metric_value,
            "timestamp": random.randint(1500000000, 1900000000)
        }

        self.engine.set_threshold_rule(metric_name, max_val=metric_value - 1)

        with self.assertRaises(RuleViolationError):
            self.engine.evaluate_telemetry(snapshot)

if __name__ == '__main__':
    unittest.main()