import unittest
import uuid
import random
from skills.market_portfolio_stress_monte_carlo_engine import generate_monte_carlo_scenarios
from skills.db_storage import save_tail_risk_metrics, get_tail_risk_metrics
from skills.market_portfolio_stress_extreme_tail_risk_model import TailRiskModel, calculate_extreme_tail_risk, TailRiskCalculationError

class TestTailRiskModelIntegration(unittest.TestCase):
    def test_end_to_end_tail_risk_calculation_and_persistence(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence_level = round(random.uniform(0.90, 0.99), 2)
        simulations = random.randint(100, 500)

        monte_carlo_engine = type('MCStub', (), {
            'generate_scenarios': staticmethod(lambda portfolio_id, paths: [random.uniform(-0.15, 0.05) for _ in range(paths)])
        })

        db_stub = type('DBStub', (), {
            'save_risk_report': staticmethod(lambda report: True)
        })

        model = TailRiskModel(db_storage=db_stub, market_portfolio_stress_monte_carlo_engine=monte_carlo_engine)

        metrics = model.calculate_expected_shortfall(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level,
            simulations=simulations
        )

        self.assertIn("expected_shortfall", metrics)
        self.assertIn("var_at_level", metrics)
        self.assertEqual(metrics["portfolio_id"], portfolio_id)

        is_persisted = model.persist_tail_risk_report(metrics)
        self.assertTrue(is_persisted)

        random_scenarios = [random.uniform(-0.2, 0.1) for _ in range(50)]
        direct_calc = calculate_extreme_tail_risk(
            portfolio_id=portfolio_id,
            scenario_data=random_scenarios,
            confidence=confidence_level
        )

        self.assertEqual(direct_calc["portfolio_id"], portfolio_id)
        self.assertIsInstance(direct_calc["expected_shortfall"], float)
        self.assertIsInstance(direct_calc["var_metric"], float)

    def test_tail_risk_calculation_empty_scenarios_raises_error(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"

        monte_carlo_empty_engine = type('MCEmptyStub', (), {
            'generate_scenarios': staticmethod(lambda portfolio_id, paths: [])
        })

        model = TailRiskModel(market_portfolio_stress_monte_carlo_engine=monte_carlo_empty_engine)

        with self.assertRaises(TailRiskCalculationError):
            model.calculate_expected_shortfall(
                portfolio_id=portfolio_id,
                confidence_level=0.95,
                simulations=100
            )

        with self.assertRaises(TailRiskCalculationError):
            calculate_extreme_tail_risk(
                portfolio_id=portfolio_id,
                scenario_data=[],
                confidence=0.95
            )

if __name__ == "__main__":
    unittest.main()