import unittest
import uuid
import random
import os
from skills.none import (
    db_storage,
    market_parser,
    market_portfolio_collector_agent,
    market_portfolio_strategy_optimizer,
    market_portfolio_scenario_simulator,
    market_portfolio_stress_monte_carlo_engine,
    market_report_generator
)

class TestArchitectureLongTermVectorIntegration(unittest.TestCase):
    def test_long_term_vector_development_cycle(self):
        run_id = str(uuid.uuid4())
        test_asset = f"ASSET_{random.randint(1000, 9999)}"
        market_data_points = random.randint(50, 200)

        raw_market_data = market_parser(target=test_asset, limit=market_data_points)
        self.assertIsNotNone(raw_market_data)

        collected_portfolio = market_portfolio_collector_agent(data=raw_market_data, session_id=run_id)
        self.assertIn("status", collected_portfolio)

        optimized_strategy = market_portfolio_strategy_optimizer(portfolio=collected_portfolio, risk_tolerance=random.uniform(0.01, 0.05))
        self.assertIsInstance(optimized_strategy, dict)

        simulation_results = market_portfolio_scenario_simulator(strategy=optimized_strategy, horizon_months=random.randint(12, 60))
        self.assertIn("simulation_id", simulation_results)

        stress_test_metrics = market_portfolio_stress_monte_carlo_engine(simulation_data=simulation_results, iterations=random.randint(100, 500))
        self.assertIsNotNone(stress_test_metrics)

        vector_report_path = f"report_vector_{run_id}.json"
        report_output = market_report_generator(
            metrics=stress_test_metrics,
            vector_id=run_id,
            output_file=vector_report_path
        )
        self.assertEqual(report_output, vector_report_path)

        db_storage(record_id=run_id, payload=stress_test_metrics)

        self.assertTrue(os.path.exists(vector_report_path), "Интеграционный цикл не создал итоговый файл отчета по новому вектору.")

        if os.path.exists(vector_report_path):
            os.remove(vector_report_path)

if __name__ == "__main__":
    unittest.main()