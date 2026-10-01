import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_stress_tail_risk_mitigator import (
    TailRiskMitigator,
    evaluate_tail_risk_and_mitigate
)


class TestMarketPortfolioStressTailRiskMitigator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.shock = random.uniform(0.01, 0.5)
        self.iters = random.randint(100, 5000)
        self.capital = random.uniform(10000.0, 1000000.0)
        self.confidence = random.uniform(0.90, 0.99)

    def test_tail_risk_mitigator_default_engine(self):
        mitigator = TailRiskMitigator()
        mock_sim_result = {"expected_shortfall": random.uniform(5000.0, 50000.0)}

        with patch('skills.market_portfolio_stress_tail_risk_mitigator.run_monte_carlo_simulation', return_value=mock_sim_result) as mock_run:
            result = mitigator.evaluate_and_mitigate(self.portfolio_id, self.shock, self.iters)

            mock_run.assert_called_once_with(portfolio_id=self.portfolio_id, runs=self.iters)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["mitigation_allocation"], mock_sim_result["expected_shortfall"] * 0.15)
            self.assertEqual(result["status"], "SECURED")

    def test_tail_risk_mitigator_injected_engine(self):
        expected_shortfall_val = random.uniform(1000.0, 20000.0)
        mock_engine = MagicMock()
        mock_engine.run_simulation.return_value = {"expected_shortfall": expected_shortfall_val}

        mitigator = TailRiskMitigator(deps={"market_portfolio_stress_monte_carlo_engine": mock_engine})
        result = mitigator.evaluate_and_mitigate(self.portfolio_id, self.shock, self.iters)

        mock_engine.run_simulation.assert_called_once_with(self.portfolio_id, self.shock, self.iters)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["mitigation_allocation"], expected_shortfall_val * 0.15)
        self.assertEqual(result["status"], "SECURED")

    def test_io_stream_handling_with_garbage(self):
        mitigator = TailRiskMitigator()
        garbage_data = uuid.uuid4().bytes + b'_' + str(random.randint(1, 1000)).encode()
        stream = io.BytesIO(garbage_data)

        length = mitigator.process_stream(stream)
        self.assertEqual(length, len(garbage_data))

    def test_evaluate_tail_risk_and_mitigate_with_dict(self):
        expected_shortfall_val = random.uniform(5000.0, 30000.0)
        simulation_data = {"expected_shortfall": expected_shortfall_val}

        result = evaluate_tail_risk_and_mitigate(
            portfolio_id=self.portfolio_id,
            capital=self.capital,
            confidence=self.confidence,
            simulation_data=simulation_data
        )

        expected_allocation = expected_shortfall_val * (1.0 - self.confidence)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["capital"], self.capital)
        self.assertEqual(result["confidence"], self.confidence)
        self.assertEqual(result["mitigation_allocation"], expected_allocation)
        self.assertEqual(result["status"], "PROCESSED")
        self.assertIn("mitigation_id", result)

    def test_evaluate_tail_risk_and_mitigate_without_dict(self):
        simulation_data = uuid.uuid4().hex

        result = evaluate_tail_risk_and_mitigate(
            portfolio_id=self.portfolio_id,
            capital=self.capital,
            confidence=self.confidence,
            simulation_data=simulation_data
        )

        default_shortfall = self.capital * 0.1
        expected_allocation = default_shortfall * (1.0 - self.confidence)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["capital"], self.capital)
        self.assertEqual(result["confidence"], self.confidence)
        self.assertEqual(result["mitigation_allocation"], expected_allocation)
        self.assertEqual(result["status"], "PROCESSED")


if __name__ == "__main__":
    unittest.main()