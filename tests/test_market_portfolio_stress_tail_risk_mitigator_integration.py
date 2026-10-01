import unittest
import uuid
import random
import io

from skills.market_portfolio_stress_tail_risk_mitigator import (
    TailRiskMitigator,
    evaluate_tail_risk_and_mitigate
)
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation


class TestTailRiskMitigatorIntegration(unittest.TestCase):

    def test_tail_risk_mitigator_real_flow(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        shock = round(random.uniform(0.05, 0.5), 4)
        iters = random.randint(10, 100)
        capital = round(random.uniform(50000.0, 500000.0), 2)
        confidence = round(random.uniform(0.90, 0.99), 2)

        # Реальный вызов связанного навыка без моков
        mc_result = run_monte_carlo_simulation(portfolio_id=portfolio_id, runs=iters)
        self.assertIsInstance(mc_result, dict)

        mitigator = TailRiskMitigator()
        evaluation = mitigator.evaluate_and_mitigate(portfolio_id=portfolio_id, shock=shock, iters=iters)

        self.assertEqual(evaluation["portfolio_id"], portfolio_id)
        self.assertEqual(evaluation["status"], "SECURED")
        self.assertIn("mitigation_allocation", evaluation)
        self.assertGreater(evaluation["mitigation_allocation"], 0.0)

        sim_data = {"expected_shortfall": evaluation["mitigation_allocation"]}
        integrated_result = evaluate_tail_risk_and_mitigate(
            portfolio_id=portfolio_id,
            capital=capital,
            confidence=confidence,
            simulation_data=sim_data
        )

        self.assertIsInstance(integrated_result.get("mitigation_id"), str)
        self.assertEqual(integrated_result["portfolio_id"], portfolio_id)
        self.assertEqual(integrated_result["capital"], capital)
        self.assertEqual(integrated_result["confidence"], confidence)
        self.assertEqual(integrated_result["status"], "PROCESSED")
        self.assertGreaterEqual(integrated_result["mitigation_allocation"], 0.0)

        stream_data = f"stream-data-{uuid.uuid4()}".encode("utf-8")
        stream = io.BytesIO(stream_data)
        stream_len = mitigator.process_stream(stream)
        self.assertEqual(stream_len, len(stream_data))


if __name__ == "__main__":
    unittest.main()