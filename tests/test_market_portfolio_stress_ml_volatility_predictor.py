import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
from skills.market_portfolio_stress_ml_volatility_predictor import (
    predict_volatility,
    train_model,
    evaluate_anomaly,
    market_portfolio_stress_ml_volatility_predictor
)


class TestMarketPortfolioStressMlVolatilityPredictor(unittest.TestCase):

    def test_predict_volatility_random(self):
        token_str = uuid.uuid4().hex
        threshold_val = round(random.uniform(0.01, 1.0), 4)
        input_data = {
            "token": token_str,
            "threshold": threshold_val
        }
        result = predict_volatility(input_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["metric"], f"volatility_{token_str[:6]}")
        self.assertEqual(result["value"], float(threshold_val))

    def test_train_model_with_stream(self):
        random_bytes = "".join(random.choices(string.ascii_letters, k=32)).encode("utf-8")
        stream_mock = io.BytesIO(random_bytes)
        res = train_model(stream_mock)
        self.assertTrue(res)

    def test_train_model_without_stream(self):
        dummy_obj = object()
        res = train_model(dummy_obj)
        self.assertTrue(res)

    def test_evaluate_anomaly_random(self):
        anomaly_identifier = uuid.uuid4().hex
        payload = {"anomaly_id": anomaly_identifier}
        res = evaluate_anomaly(payload)
        self.assertEqual(res, anomaly_identifier)

    def test_market_portfolio_stress_ml_volatility_predictor_integration(self):
        portfolio_id = uuid.uuid4().hex
        stress_mult = round(random.uniform(1.0, 5.0), 2)
        historical_horizon = random.randint(10, 500)

        simulation_data = {
            "stress_multiplier": stress_mult
        }

        expected_volatility = 0.05 * (stress_mult * (1.0 + historical_horizon / 1000.0))

        with patch("skills.market_portfolio_stress_ml_volatility_predictor.db_storage") as mock_db:
            output = market_portfolio_stress_ml_volatility_predictor(
                portfolio_id, simulation_data, historical_horizon
            )

            self.assertIsInstance(output, dict)
            self.assertEqual(output["portfolio_id"], portfolio_id)
            self.assertAlmostEqual(output["predicted_volatility"], float(expected_volatility))
            self.assertEqual(output["horizon"], historical_horizon)

            mock_db.assert_called_once()
            called_args = mock_db.call_args[1]
            self.assertEqual(called_args.get("action"), "save_prediction")
            self.assertEqual(called_args.get("target_id"), portfolio_id)
            self.assertEqual(called_args.get("payload"), output)