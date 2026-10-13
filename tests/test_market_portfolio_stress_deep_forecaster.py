import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_deep_forecaster import start_new, market_portfolio_stress_deep_forecaster


class TestMarketPortfolioStressDeepForecaster(unittest.TestCase):

    def test_start_new_success_flow(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_conf = round(random.uniform(0.8, 0.99), 2)
        rand_hist_data = [random.randint(100, 500) for _ in range(3)]
        rand_scenario_res = {f"sc_{uuid.uuid4().hex[:4]}": random.random()}
        rand_anomaly = {f"an_{uuid.uuid4().hex[:4]}": random.randint(1, 10)}
        rand_ml_pred = round(random.uniform(0.1, 0.9), 4)
        rand_audit_id = f"aud_{uuid.uuid4().hex[:8]}"

        with patch("skills.market_portfolio_stress_deep_forecaster.db_storage") as mock_db, \
             patch("skills.market_portfolio_stress_deep_forecaster.market_portfolio_scenario_simulator") as mock_sim, \
             patch("skills.market_portfolio_stress_deep_forecaster.market_anomaly_detector") as mock_anomaly, \
             patch("skills.market_portfolio_stress_deep_forecaster.market_portfolio_ml_stress_evaluator") as mock_ml, \
             patch("skills.market_portfolio_stress_deep_forecaster.market_portfolio_stress_audit_exporter_v2") as mock_audit:

            mock_db.fetch_historical_data.return_value = rand_hist_data
            mock_sim.run_matrix.return_value = rand_scenario_res
            mock_anomaly.evaluate_anomalies.return_value = rand_anomaly
            mock_ml.predict_stress.return_value = rand_ml_pred
            mock_audit.export_audit_log.return_value = rand_audit_id

            result = start_new(portfolio_id=rand_portfolio_id, confidence=rand_conf)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "success")
            self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
            self.assertEqual(result.get("confidence"), rand_conf)
            self.assertEqual(result.get("historical_data"), rand_hist_data)
            self.assertEqual(result.get("scenario_result"), rand_scenario_res)
            self.assertEqual(result.get("ml_stress_prediction"), rand_ml_pred)
            self.assertEqual(result.get("audit_id"), rand_audit_id)
            self.assertEqual(result.get("anomaly_analysis"), rand_anomaly)

    def test_start_new_exception_handling(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_error_msg = f"err_{uuid.uuid4().hex[:6]}"

        with patch("skills.market_portfolio_stress_deep_forecaster.db_storage", side_effect=Exception(rand_error_msg)):
            result = start_new(portfolio_id=rand_portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertEqual(result["error"], rand_error_msg)

    def test_market_portfolio_stress_deep_forecaster_integration(self):
        rand_portfolio_id = f"port_int_{uuid.uuid4().hex[:8]}"
        rand_insights = {f"ins_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        rand_evals = {f"ev_{uuid.uuid4().hex[:4]}": random.random()}

        with patch("skills.market_portfolio_stress_deep_forecaster.db_storage") as mock_db:
            mock_db.side_effect = lambda **kwargs: kwargs.get("record_id")

            result = market_portfolio_stress_deep_forecaster(
                portfolio_id=rand_portfolio_id,
                anomaly_insights=rand_insights,
                scenario_evaluations=rand_evals
            )

            self.assertIsInstance(result, dict)
            self.assertIn("forecast_id", result)
            self.assertEqual(result.get("portfolio_id"), rand_portfolio_id)
            self.assertEqual(result.get("anomaly_insights"), rand_insights)
            self.assertEqual(result.get("scenario_evaluations"), rand_evals)
            self.assertIsInstance(result.get("stress_probability"), float)


if __name__ == "__main__":
    unittest.main()