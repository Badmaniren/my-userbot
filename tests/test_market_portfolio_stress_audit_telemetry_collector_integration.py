import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_telemetry_collector import (
    market_portfolio_stress_audit_telemetry_collector
)
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway

class TestMarketPortfolioStressAuditTelemetryCollectorIntegration(unittest.TestCase):
    def test_stress_audit_telemetry_collector_pipeline(self):
        portfolio_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        metric_value = round(random.uniform(10500.50, 99999.99), 2)
        volatility_index = round(random.uniform(0.1, 0.9), 4)

        gateway_payload = {
            "session_id": session_id,
            "portfolio_id": portfolio_id,
            "initial_capital": metric_value,
            "volatility": volatility_index
        }

        gateway_response = market_portfolio_api_gateway(gateway_payload)
        self.assertIsNotNone(gateway_response)

        agent_data = market_portfolio_collector_agent(portfolio_id)
        self.assertIsNotNone(agent_data)

        telemetry_input = {
            "session_id": session_id,
            "portfolio_id": portfolio_id,
            "metrics": agent_data,
            "gateway_ref": gateway_response
        }

        collected_telemetry = market_portfolio_stress_audit_telemetry_collector(telemetry_input)
        self.assertIsInstance(collected_telemetry, dict)
        self.assertIn("telemetry_id", collected_telemetry)

        telemetry_id = collected_telemetry["telemetry_id"]
        self.assertTrue(len(telemetry_id) > 0)

        db_record = db_storage(telemetry_id)
        self.assertIsNotNone(db_record)
        self.assertEqual(db_record.get("portfolio_id"), portfolio_id)
        self.assertEqual(db_record.get("session_id"), session_id)

if __name__ == "__main__":
    unittest.main()