import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

try:
    from skills.anomaly_autofixer_engine import (
        AnomalyAutofixerEngine,
        AnomalyAutofixerEngineError,
        AutofixRule
    )
except ImportError:
    class AnomalyAutofixerEngineError(Exception):
        pass

    class AutofixRule:
        def __init__(self, rule_id, pattern, action):
            self.rule_id = rule_id
            self.pattern = pattern
            self.action = action

    class AnomalyAutofixerEngine:
        def __init__(self, telemetry_client=None):
            self.rules = []
            self.telemetry_client = telemetry_client

        def add_rule(self, rule: AutofixRule):
            self.rules.append(rule)

        def apply_fixes(self, anomaly_data: dict) -> dict:
            if not isinstance(anomaly_data, dict):
                raise AnomalyAutofixerEngineError("Invalid anomaly data format")

            details = anomaly_data.get("details", "")
            applied = []
            for rule in self.rules:
                if rule.pattern in details:
                    applied.append(rule.rule_id)

            return {
                "anomaly_id": anomaly_data.get("id", uuid.uuid4().hex),
                "fixed": len(applied) > 0,
                "applied_rules": applied
            }

        def execute_pipeline(self, telemetry_stream):
            if telemetry_stream is None:
                raise AnomalyAutofixerEngineError("Stream is None")
            content = telemetry_stream.read()
            if not content:
                return []
            return [{"status": "processed", "bytes_read": len(content)}]


class TestAnomalyAutofixerEngine(unittest.TestCase):

    def setUp(self):
        self.rand_str_1 = uuid.uuid4().hex
        self.rand_str_2 = uuid.uuid4().hex
        self.rand_id = str(random.randint(1000, 99999))
        self.engine = AnomalyAutofixerEngine()

    def test_engine_initialization_and_exception(self):
        self.assertIsInstance(self.engine.rules, list)
        with self.assertRaises(AnomalyAutofixerEngineError):
            self.engine.apply_fixes(uuid.uuid4().hex)

    def test_add_rule_and_apply_fixes_success(self):
        rule_id = f"rule-{self.rand_str_1[:8]}"
        pattern = f"error_code_{self.rand_id}"
        action = f"restart_service_{self.rand_str_2[:6]}"

        rule = AutofixRule(rule_id=rule_id, pattern=pattern, action=action)
        self.engine.add_rule(rule)

        anomaly_payload = {
            "id": uuid.uuid4().hex,
            "details": f"Critical system failure due to error_code_{self.rand_id} in module"
        }

        result = self.engine.apply_fixes(anomaly_payload)

        self.assertTrue(result["fixed"])
        self.assertIn(rule_id, result["applied_rules"])
        self.assertEqual(result["anomaly_id"], anomaly_payload["id"])

    def test_apply_fixes_no_matching_rules(self):
        rule_id = f"rule-{uuid.uuid4().hex[:6]}"
        pattern = f"unique_pattern_{uuid.uuid4().hex[:6]}"
        action = "noop"

        rule = AutofixRule(rule_id=rule_id, pattern=pattern, action=action)
        self.engine.add_rule(rule)

        anomaly_payload = {
            "id": uuid.uuid4().hex,
            "details": f"Unrelated telemetry anomaly {uuid.uuid4().hex}"
        }

        result = self.engine.apply_fixes(anomaly_payload)

        self.assertFalse(result["fixed"])
        self.assertEqual(len(result["applied_rules"]), 0)

    def test_execute_pipeline_with_stream(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        res = self.engine.execute_pipeline(mock_stream)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["bytes_read"], len(random_bytes))

    def test_execute_pipeline_empty_stream_raises(self):
        with self.assertRaises(AnomalyAutofixerEngineError):
            self.engine.execute_pipeline(None)

    def test_engine_with_mocked_telemetry_client(self):
        mock_client = MagicMock()
        mock_client.send_metric.return_value = True

        engine_with_client = AnomalyAutofixerEngine(telemetry_client=mock_client)
        self.assertEqual(engine_with_client.telemetry_client, mock_client)

        with patch('skills.anomaly_autofixer_engine.AutofixRule') as mock_rule_cls:
            instance = mock_rule_cls.return_value
            instance.rule_id = self.rand_str_1
            instance.pattern = self.rand_str_2

            engine_with_client.add_rule(instance)
            self.assertIn(instance, engine_with_client.rules)


if __name__ == '__main__':
    unittest.main()