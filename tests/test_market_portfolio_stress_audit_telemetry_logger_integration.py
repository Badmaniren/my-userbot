import unittest
import uuid
import random
import time

from skills.market_portfolio_stress_audit_telemetry_logger import (
    StressAuditTelemetryLogger,
    TelemetryLoggingError,
    market_portfolio_stress_audit_telemetry_logger
)
from skills import market_portfolio_collector_agent
from skills import market_portfolio_stress_scenario_pipeline
from skills import db_storage


class TestMarketPortfolioStressAuditTelemetryLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self.logger_instance = StressAuditTelemetryLogger()

    def test_end_to_end_stress_audit_telemetry_pipeline(self):
        random_assets_count = random.randint(1, 5)
        raw_collector_data = {"portfolio_id": self.portfolio_id, "status": "collected"}

        self.assertIsInstance(raw_collector_data, dict)

        simulated_shocks = [round(random.uniform(-0.5, -0.1), 4) for _ in range(random_assets_count)]
        raw_pipeline_data = {"portfolio_id": self.portfolio_id, "shocks": simulated_shocks}

        self.assertIsInstance(raw_pipeline_data, dict)

        telemetry_meta = {
            "audit_id": self.audit_id,
            "initiated_by": f"user_{uuid.uuid4().hex[:6]}",
            "execution_index": random.randint(100, 999)
        }

        logger_result = market_portfolio_stress_audit_telemetry_logger(
            portfolio_id=self.portfolio_id,
            collector_data=raw_collector_data,
            pipeline_data=raw_pipeline_data,
            telemetry_meta=telemetry_meta
        )

        self.assertIsInstance(logger_result, dict)
        self.assertEqual(logger_result.get("status"), "logged")
        self.assertEqual(logger_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(logger_result.get("audit_id"), self.audit_id)

    def test_stress_audit_telemetry_logger_class_methods_integration(self):
        dynamic_payload = {
            "metric_name": f"stress_drawdown_{uuid.uuid4().hex[:4]}",
            "value": round(random.uniform(10.0, 99.9), 2),
            "timestamp": time.time()
        }

        dispatch_res = self.logger_instance.dispatch_audit_telemetry(dynamic_payload)
        self.assertIsInstance(dispatch_res, dict)
        self.assertIn("timestamp", dispatch_res)

        log_success = self.logger_instance.log_telemetry(dispatch_res)
        self.assertTrue(log_success)

        with self.assertRaises(TelemetryLoggingError):
            self.logger_instance.log_telemetry({})

        with self.assertRaises(TelemetryLoggingError):
            self.logger_instance.consume_telemetry_stream("not_a_stream_object")


if __name__ == "__main__":
    unittest.main()
