import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_governance_ledger import (
    db_storage,
    market_portfolio_scenario_simulator,
    market_portfolio_stress_monte_carlo_engine,
    market_portfolio_stress_reporter,
    market_portfolio_stress_governance_ledger
)

class TestMarketPortfolioStressGovernanceLedgerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, f"test_ledger_{uuid.uuid4()}.db")
        self.storage = db_storage(self.db_path)

        self.portfolio_id = str(uuid.uuid4())
        self.simulation_seed = random.randint(1000, 99999)
        self.shock_percentage = round(random.uniform(5.0, 45.0), 2)
        self.confidence_level = random.choice([0.95, 0.99])

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_governance_ledger_end_to_end(self):
        simulator = market_portfolio_scenario_simulator()
        sim_result = simulator.run_scenario(
            portfolio_id=self.portfolio_id,
            shock=self.shock_percentage,
            seed=self.simulation_seed
        )
        self.assertIsNotNone(sim_result)

        mc_engine = market_portfolio_stress_monte_carlo_engine()
        mc_metrics = mc_engine.evaluate(
            portfolio_id=self.portfolio_id,
            confidence=self.confidence_level,
            iterations=1000
        )
        self.assertIn("var", mc_metrics)

        ledger = market_portfolio_stress_governance_ledger(storage=self.storage)
        record_id = ledger.commit_simulation_audit(
            portfolio_id=self.portfolio_id,
            simulation_data=sim_result,
            monte_carlo_metrics=mc_metrics
        )
        self.assertIsInstance(record_id, str)
        self.assertTrue(len(record_id) > 0)

        reporter = market_portfolio_stress_reporter(storage=self.storage)
        report_payload = reporter.generate_compliance_report(portfolio_id=self.portfolio_id)

        self.assertIn(self.portfolio_id, str(report_payload))

        stored_audit = self.storage.get_record(record_id)
        self.assertEqual(stored_audit["portfolio_id"], self.portfolio_id)
        self.assertEqual(stored_audit["simulation_seed"], self.simulation_seed)

if __name__ == "__main__":
    unittest.main()