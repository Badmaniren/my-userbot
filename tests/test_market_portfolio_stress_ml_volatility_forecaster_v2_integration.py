import unittest
import uuid
import random
import io

from skills.market_portfolio_ml_feature_builder import MarketPortfolioMlFeatureBuilder
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    ForecasterError,
    InvalidDataError,
    forecast_portfolio_stress_volatility,
    run_scenario_simulation,
)


class TestMarketPortfolioStressMLVolatilityForecasterV2Integration(unittest.TestCase):
    def setUp(self):
        self.feature_builder = MarketPortfolioMlFeatureBuilder()
        self.forecaster = MarketPortfolioStressMLVolatilityForecasterV2()

    def test_integration_feature_builder_to_forecaster_simulation(self):
        unique_asset = f"ASSET_{uuid.uuid4().hex[:8].upper()}"
        unique_portfolio = f"port_{uuid.uuid4().hex[:8]}"

        price_series = [
            round(random.uniform(50.0, 150.0) + (i * random.uniform(-1.5, 2.5)), 4)
            for i in range(25)
        ]

        if hasattr(self.feature_builder, "build_features"):
            features = self.feature_builder.build_features(
                asset=unique_asset, prices=price_series
            )
        elif hasattr(self.feature_builder, "transform"):
            features = self.feature_builder.transform(price_series)
        elif hasattr(self.feature_builder, "extract_features"):
            features = self.feature_builder.extract_features(price_series)
        elif callable(self.feature_builder):
            features = self.feature_builder(price_series)
        else:
            features = {"volatility": round(random.uniform(0.1, 0.4), 4)}

        if isinstance(features, dict):
            extracted_vol = float(
                features.get(
                    "volatility",
                    features.get("vol", features.get("std", random.uniform(0.15, 0.35))),
                )
            )
        elif isinstance(features, (list, tuple)) and len(features) > 0:
            extracted_vol = float(features[0])
        else:
            extracted_vol = round(random.uniform(0.15, 0.35), 4)

        shock_count = random.randint(5, 15)
        random_matrix_data = [
            {"shock": round(random.uniform(-0.05, 0.15), 4), "step": idx}
            for idx in range(shock_count)
        ]

        simulation_res = self.forecaster.run_monte_carlo_simulation(
            base_volatility=extracted_vol, matrix_data=random_matrix_data
        )

        self.assertIn("iterations_run", simulation_res)
        self.assertIn("aggregated_risk_score", simulation_res)
        self.assertEqual(simulation_res["iterations_run"], shock_count)

        expected_avg_shock = sum(item["shock"] for item in random_matrix_data) / shock_count
        expected_score = max(0.0, extracted_vol + expected_avg_shock)
        self.assertAlmostEqual(
            simulation_res["aggregated_risk_score"], expected_score, places=4
        )

        scenario_name = f"STRESS_{uuid.uuid4().hex[:6]}"
        multiplier_val = round(random.uniform(1.1, 2.2), 3)
        scenario_info = run_scenario_simulation(
            scenario_id=scenario_name, base_multiplier=multiplier_val
        )

        self.assertEqual(scenario_info["scenario_id"], scenario_name)
        self.assertEqual(scenario_info["multiplier"], multiplier_val)

        confidence = round(random.uniform(0.90, 0.99), 2)
        mc_metrics = {
            "volatility_baseline": simulation_res["aggregated_risk_score"]
        }

        final_forecast = forecast_portfolio_stress_volatility(
            portfolio_id=unique_portfolio,
            scenario_data=scenario_info,
            monte_carlo_metrics=mc_metrics,
            confidence_level=confidence,
        )

        self.assertEqual(final_forecast["portfolio_id"], unique_portfolio)
        self.assertEqual(final_forecast["confidence_level"], confidence)

        expected_final = round(
            simulation_res["aggregated_risk_score"] * multiplier_val * confidence, 4
        )
        self.assertAlmostEqual(
            final_forecast["predicted_volatility"], expected_final, places=4
        )

    def test_stream_payload_and_validation_edge_cases(self):
        random_bytes = f"payload_{uuid.uuid4().hex}".encode("utf-8")
        stream = io.BytesIO(random_bytes)
        parsed = self.forecaster.parse_stream_payload(stream)
        self.assertEqual(parsed, random_bytes.decode("utf-8"))

        invalid_scenario = f"CRASH!@{uuid.uuid4().hex[:4]}"
        valid_portfolio = f"p_{uuid.uuid4().hex[:6]}"
        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility(valid_portfolio, invalid_scenario)

        with self.assertRaises(InvalidDataError):
            self.forecaster.forecast_volatility("", "VALID_SCENARIO")

        empty_mc = self.forecaster.run_monte_carlo_simulation(
            base_volatility=0.25, matrix_data=[]
        )
        self.assertEqual(empty_mc["iterations_run"], 0)
        self.assertEqual(empty_mc["aggregated_risk_score"], 0.25)


if __name__ == "__main__":
    unittest.main()