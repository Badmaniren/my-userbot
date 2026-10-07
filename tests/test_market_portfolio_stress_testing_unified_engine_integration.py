import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_stress_testing_unified_engine import (
    market_portfolio_stress_testing_unified_engine
)
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
from skills.db_storage import db_storage

class TestMarketPortfolioStressTestingUnifiedEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.test_asset = f"ASST_{random.choice(['AAPL', 'BTC', 'ETH', 'TSLA', 'SPY'])}"
        self.initial_capital = round(random.uniform(50000.0, 1000000.0), 2)
        self.simulation_runs = random.randint(100, 1000)
        self.stress_factor = round(random.uniform(0.1, 0.5), 4)

    def test_unified_stress_testing_engine_end_to_end(self):
        collector_input = {
            "portfolio_id": self.portfolio_id,
            "asset": self.test_asset,
            "amount": self.initial_capital,
            "timestamp": uuid.uuid1().int
        }
        collected_data = market_portfolio_collector_agent(collector_input)
        self.assertIsNotNone(collected_data)

        valuation_input = {
            "portfolio_id": self.portfolio_id,
            "data": collected_data
        }
        valuation_result = market_portfolio_valuation(valuation_input)
        self.assertIn("valuation", valuation_result or {})

        mc_input = {
            "portfolio_id": self.portfolio_id,
            "runs": self.simulation_runs,
            "base_valuation": valuation_result.get("valuation", self.initial_capital)
        }
        monte_carlo_results = market_portfolio_stress_monte_carlo_engine(mc_input)
        self.assertIsNotNone(monte_carlo_results)

        scenario_input = {
            "portfolio_id": self.portfolio_id,
            "stress_factor": self.stress_factor,
            "valuation": valuation_result
        }
        scenario_results = market_portfolio_scenario_simulator(scenario_input)
        self.assertIsNotNone(scenario_results)

        audit_input = {
            "portfolio_id": self.portfolio_id,
            "monte_carlo": monte_carlo_results,
            "scenarios": scenario_results
        }
        audit_results = market_portfolio_audit_compliance_hub(audit_input)
        self.assertIsNotNone(audit_results)

        unified_engine_payload = {
            "portfolio_id": self.portfolio_id,
            "monte_carlo_data": monte_carlo_results,
            "scenario_data": scenario_results,
            "audit_data": audit_results,
            "run_id": uuid.uuid4().hex
        }

        engine_output = market_portfolio_stress_testing_unified_engine(unified_engine_payload)

        self.assertIsInstance(engine_output, dict)
        self.assertEqual(engine_output.get("portfolio_id"), self.portfolio_id)
        self.assertIn("unified_stress_score", engine_output)
        self.assertIn("audit_status", engine_output)

        db_record = db_storage({
            "action": "get",
            "portfolio_id": self.portfolio_id,
            "module": "stress_testing_unified_engine"
        })

        if db_record is not None:
            self.assertEqual(db_record.get("portfolio_id"), self.portfolio_id)

if __name__ == "__main__":
    unittest.main()