import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_governance_ledger_v2 import (
    market_portfolio_stress_governance_ledger_v2
)
from skills.db_storage import db_storage
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine

class TestMarketPortfolioStressGovernanceLedgerV2Integration(unittest.TestCase):
    def test_stress_governance_ledger_end_to_end(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        stress_factor = round(random.uniform(0.05, 0.5), 4)
        simulations_count = random.randint(100, 1000)

        pipeline_res = market_portfolio_stress_scenario_pipeline(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            intensity=stress_factor
        )
        self.assertIsNotNone(pipeline_res)

        mc_res = market_portfolio_stress_monte_carlo_engine(
            scenario_id=scenario_id,
            simulations=simulations_count
        )
        self.assertIsNotNone(mc_res)

        audit_record_id = f"audit_{uuid.uuid4().hex}"
        ledger_result = market_portfolio_stress_governance_ledger_v2(
            audit_id=audit_record_id,
            portfolio_id=portfolio_id,
            scenario_data=pipeline_res,
            monte_carlo_data=mc_res
        )

        self.assertIsInstance(ledger_result, dict)
        self.assertEqual(ledger_result.get("audit_id"), audit_record_id)
        self.assertEqual(ledger_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(ledger_result.get("status"), "COMMITTED")

        stored_data = db_storage(action="get", key=audit_record_id)
        self.assertIsNotNone(stored_data)
        if isinstance(stored_data, dict):
            self.assertEqual(stored_data.get("audit_id"), audit_record_id)

if __name__ == "__main__":
    unittest.main()