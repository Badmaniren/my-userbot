import unittest
import uuid
import random
import string
import io
from unittest.mock import patch, MagicMock

from skills.market_portfolio_stress_audit_resilience_guard import (
    MarketPortfolioStressAuditResilienceGuard,
    market_portfolio_stress_audit_resilience_guard
)


class TestMarketPortfolioStressAuditResilienceGuard(unittest.TestCase):

    def setUp(self):
        self.random_scenario_id = uuid.uuid4().hex
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')

        self.guard_instance = MarketPortfolioStressAuditResilienceGuard(
            config_key=uuid.uuid4().hex,
            timeout=random.randint(10, 100)
        )

    def test_audit_integrity_and_validate_success(self):
        result = self.guard_instance.audit_integrity_and_validate(
            report_payload=self.random_payload,
            scenario_id=self.random_scenario_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "SECURE_INTEGRITY_VERIFIED")
        self.assertEqual(result.get("scenario_id"), self.random_scenario_id)
        self.assertEqual(result.get("bytes_audited"), len(self.random_payload))
        self.assertIn("validation_token", result)
        self.assertEqual(len(result["validation_token"]), 10)

    def test_audit_integrity_and_validate_empty_payload_raises(self):
        with self.assertRaises(ValueError):
            self.guard_instance.audit_integrity_and_validate(
                report_payload=b"",
                scenario_id=self.random_scenario_id
            )

    def test_audit_integrity_and_validate_missing_scenario_raises(self):
        with self.assertRaises(ValueError):
            self.guard_instance.audit_integrity_and_validate(
                report_payload=self.random_payload,
                scenario_id=""
            )

    def test_functional_guard_with_nested_scenario_data(self):
        guard_input = {
            "audit_report": {
                "scenario_data": {
                    "portfolio_id": self.random_portfolio_id
                }
            },
            "expected_portfolio_id": uuid.uuid4().hex
        }

        result = market_portfolio_stress_audit_resilience_guard(guard_input)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("is_resilient"))
        self.assertEqual(result.get("verified_portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("audit_score"), 1.0)

    def test_functional_guard_fallback_to_root_portfolio_id(self):
        guard_input = {
            "audit_report": {
                "portfolio_id": self.random_portfolio_id
            },
            "expected_portfolio_id": uuid.uuid4().hex
        }

        result = market_portfolio_stress_audit_resilience_guard(guard_input)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("is_resilient"))
        self.assertEqual(result.get("verified_portfolio_id"), self.random_portfolio_id)
        self.assertEqual(result.get("audit_score"), 1.0)

    def test_functional_guard_fallback_to_expected_portfolio_id(self):
        expected_id = uuid.uuid4().hex
        guard_input = {
            "audit_report": {},
            "expected_portfolio_id": expected_id
        }

        result = market_portfolio_stress_audit_resilience_guard(guard_input)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("is_resilient"))
        self.assertEqual(result.get("verified_portfolio_id"), expected_id)
        self.assertEqual(result.get("audit_score"), 1.0)

    def test_guard_with_bytes_stream_payload(self):
        stream_data = io.BytesIO("".join(random.choices(string.ascii_letters, k=30)).encode('utf-8'))
        payload = stream_data.read()

        result = self.guard_instance.audit_integrity_and_validate(
            report_payload=payload,
            scenario_id=self.random_scenario_id
        )

        self.assertEqual(result["bytes_audited"], 30)
        self.assertEqual(result["scenario_id"], self.random_scenario_id)


if __name__ == "__main__":
    unittest.main()