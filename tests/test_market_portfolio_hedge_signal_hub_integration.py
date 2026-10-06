import unittest
import uuid
import random
import os
from skills.market_portfolio_hedge_signal_hub import (
    market_portfolio_hedge_signal_hub,
    db_storage,
    market_anomaly_detector,
    market_portfolio_stress_scenario_pipeline,
    market_portfolio_integration_hub
)

class TestMarketPortfolioHedgeSignalHubIntegration(unittest.TestCase):
    def test_hedge_signal_hub_real_integration(self):
        unique_run_id = str(uuid.uuid4())
        mock_portfolio_id = f"port_{random.randint(10000, 99999)}"
        stress_metric = round(random.uniform(0.01, 0.99), 4)

        anomaly_data = market_anomaly_detector(
            portfolio_id=mock_portfolio_id,
            run_token=unique_run_id,
            threshold=stress_metric
        )

        stress_pipeline_result = market_portfolio_stress_scenario_pipeline(
            payload=anomaly_data,
            mode="integration_live"
        )

        hub_evaluation = market_portfolio_integration_hub(
            input_context=stress_pipeline_result,
            validate_strict=True
        )

        signal_output = market_portfolio_hedge_signal_hub(
            context=hub_evaluation,
            signal_id=unique_run_id,
            intensity=stress_metric
        )

        self.assertIsNotNone(signal_output)
        self.assertIn("signal_id", signal_output)
        self.assertEqual(signal_output["signal_id"], unique_run_id)

        persisted_record = db_storage(
            action="get",
            key=unique_run_id
        )

        self.assertIsNotNone(persisted_record)
        self.assertEqual(persisted_record.get("portfolio_id"), mock_portfolio_id)

        target_filepath = f"hedge_signal_{unique_run_id}.log"
        self.assertTrue(
            os.path.exists(target_filepath) or persisted_record.get("logged") is True,
            "Integration must result in side effects such as file persistence or DB confirmation"
        )

        if os.path.exists(target_filepath):
            os.remove(target_filepath)

if __name__ == "__main__":
    unittest.main()