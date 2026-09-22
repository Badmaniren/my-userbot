import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_scenario_matrix import (
    db_storage,
    market_parser,
    market_portfolio_scenario_simulator,
    market_portfolio_stress_reporter,
    market_report_generator
)

class TestMarketPortfolioStressScenarioMatrixIntegration(unittest.TestCase):
    def test_stress_scenario_matrix_end_to_end(self):
        portfolio_id = str(uuid.uuid4())
        scenario_seed = random.randint(1000, 9999)
        market_shift_factor = round(random.uniform(-0.5, 0.5), 4)

        raw_market_data = market_parser.fetch_market_snapshot(seed=scenario_seed)
        self.assertIsNotNone(raw_market_data)

        simulation_config = {
            "portfolio_id": portfolio_id,
            "shift_factor": market_shift_factor,
            "data_source": raw_market_data
        }

        simulation_result = market_portfolio_scenario_simulator.run_multi_factor_simulation(simulation_config)
        self.assertIn("simulation_id", simulation_result)
        sim_id = simulation_result["simulation_id"]
        self.assertIsInstance(sim_id, str)

        matrix_report = market_portfolio_stress_reporter.generate_matrix_report(sim_id)
        self.assertIsNotNone(matrix_report)

        db_storage.save_stress_matrix(portfolio_id, matrix_report)
        stored_record = db_storage.get_stress_matrix(portfolio_id)
        self.assertEqual(stored_record["portfolio_id"], portfolio_id)

        report_file_path = f"/tmp/stress_report_{portfolio_id}.pdf"
        market_report_generator.export_to_pdf(stored_record, report_file_path)

        self.assertTrue(os.path.exists(report_file_path))
        self.assertGreater(os.path.getsize(report_file_path), 0)

        if os.path.exists(report_file_path):
            os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()