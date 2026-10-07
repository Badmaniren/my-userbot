import unittest
import uuid
import random
import io
import json
import skills.market_portfolio_stress_diagnostic_telemetry as telemetry_module

class TestMarketPortfolioStressDiagnosticTelemetryIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.session_id = f"sess_{uuid.uuid4().hex[:8]}"
        self.context_id = f"ctx_{uuid.uuid4().hex[:8]}"
        self.matrix_id = f"mat_{uuid.uuid4().hex[:8]}"
        self.stream_id = f"stream_{uuid.uuid4().hex[:8]}"
        self.db_url = f"sqlite:///:memory:"
        self.collector = telemetry_module.StressDiagnosticTelemetryCollector(db_storage_url=self.db_url)

    def test_collect_and_validate_integration(self):
        try:
            result = self.collector.collect_and_validate(self.portfolio_id, self.session_id)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(result.get("session_id"), self.session_id)
            self.assertIn("var_95", result)
            self.assertIn("stress_score", result)
        except Exception as e:
            self.fail(f"Integration failed with real engines: {e}")

    def test_market_portfolio_stress_diagnostic_telemetry_run(self):
        salt = uuid.uuid4().hex
        res = telemetry_module.market_portfolio_stress_diagnostic_telemetry_run(self.portfolio_id, salt)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertTrue(res.get("integrity_status"))
        self.assertTrue(res.get("telemetry_id").startswith("telemetry_"))

    def test_compile_financial_friction_report(self):
        try:
            report = self.collector.compile_financial_friction_report(self.portfolio_id)
            self.assertIsInstance(report, dict)
            self.assertEqual(report.get("portfolio_id"), self.portfolio_id)
            self.assertIn("tax_liability", report)
            self.assertIn("execution_cost", report)
        except Exception as e:
            self.fail(f"Financial friction compilation failed: {e}")

    def test_db_storage_helpers(self):
        record_id = f"rec_{uuid.uuid4().hex[:8]}"
        payload = {"random_val": random.random()}
        save_res = telemetry_module.db_storage_save(record_id, payload)
        self.assertIsInstance(save_res, bool)
        retrieved = telemetry_module.db_storage_get(record_id)
        self.assertIsInstance(retrieved, dict)

if __name__ == "__main__":
    unittest.main()