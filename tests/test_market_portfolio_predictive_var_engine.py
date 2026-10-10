import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine,
    VarEngineError,
    InsufficientDataError
)

class TestPredictiveVarEngine(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.anomaly_detector = MagicMock()
        
        self.engine = PredictiveVarEngine(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.anomaly_detector
        )

    def test_calculate_predictive_var_success(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        simulations_count = random.randint(100, 5000)
        horizon = random.randint(1, 30)
        confidence = round(random.uniform(0.90, 0.99), 4)

        mock_volatility_data = {
            uuid.uuid4().hex: random.uniform(0.1, 0.5),
            uuid.uuid4().hex: random.uniform(0.2, 0.8)
        }

        mock_mc_results = {
            "portfolio_id": portfolio_id,
            "simulations": simulations_count,
            "horizon_days": horizon,
            "simulated_losses": [random.uniform(-1000, 50000) for _ in range(50)]
        }

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2") as mock_forecaster_cls, \
             patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine") as mock_mc_cls:

            instance_forecaster = mock_forecaster_cls.return_value
            instance_forecaster.forecast_volatility.return_value = mock_volatility_data

            instance_mc = mock_mc_cls.return_value
            instance_mc.run_simulation.return_value = mock_mc_results

            result = self.engine.calculate_predictive_var(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations_count,
                horizon_days=horizon,
                confidence_level=confidence
            )

            self.assertIsInstance(result, dict)
            self.assertIn("var_value", result)
            self.assertIn("cvar_value", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["confidence_level"], confidence)

    def test_calculate_predictive_var_insufficient_data(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2") as mock_forecaster_cls:
            instance_forecaster = mock_forecaster_cls.return_value
            instance_forecaster.forecast_volatility.side_effect = Exception("ML model failure")

            with self.assertRaises(InsufficientDataError):
                self.engine.calculate_predictive_var(
                    portfolio_id=portfolio_id,
                    scenario_code=scenario_code,
                    simulations=random.randint(100, 1000),
                    horizon_days=random.randint(1, 10),
                    confidence_level=0.95
                )

    def test_stream_payload_processing(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")
        stream_mock = io.BytesIO(random_bytes)

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine") as mock_mc_cls:
            instance_mc = mock_mc_cls.return_value
            instance_mc.consume_stream.return_value = random_bytes.decode("utf-8")

            processed_data = self.engine.process_market_stream(stream_mock)
            self.assertIsInstance(processed_data, str)
            self.assertTrue(len(processed_data) > 0)

    def test_evaluate_var_risk_anomaly(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex
        html_content = f"<html><body><div>{uuid.uuid4().hex}</div></body></html>"

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2") as mock_forecaster_cls:
            instance_forecaster = mock_forecaster_cls.return_value
            anomaly_payload = {
                "anomaly_detected": True,
                "score": random.uniform(0.5, 1.0),
                "token": uuid.uuid4().hex
            }
            instance_forecaster.evaluate_stress_anomaly.return_value = anomaly_payload

            result = self.engine.evaluate_risk_anomaly(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                soup_content=html_content
            )

            self.assertEqual(result, anomaly_payload)
            self.assertTrue(result["anomaly_detected"])

    def test_export_predictive_audit_report(self):
        report_id = uuid.uuid4().hex
        loss_limit = round(random.uniform(10000.0, 500000.0), 2)

        expected_report = {
            "report_id": report_id,
            "status": "APPROVED",
            "threshold": loss_limit,
            "signature": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine") as mock_mc_cls:
            instance_mc = mock_mc_cls.return_value
            instance_mc.export_report.return_value = expected_report

            report = self.engine.export_predictive_audit_report(
                report_id=report_id,
                loss_limit=loss_limit
            )

            self.assertEqual(report, expected_report)
            self.assertEqual(report["report_id"], report_id)
            self.assertEqual(report["threshold"], loss_limit)

    def test_fetch_external_predictive_metrics(self):
        target_url = f"https://{uuid.uuid4().hex}.com/api/v1/metrics"
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex

        external_metrics = {
            "volatility_index": random.uniform(10.0, 35.0),
            "confidence_bound": random.uniform(0.01, 0.05),
            "reference": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2") as mock_forecaster_cls:
            instance_forecaster = mock_forecaster_cls.return_value
            instance_forecaster.fetch_external_ml_metrics.return_value = external_metrics

            metrics = self.engine.fetch_external_predictive_metrics(
                target_url=target_url,
                portfolio_id=portfolio_id,
                scenario_code=scenario_code
            )

            self.assertEqual(metrics, external_metrics)
            self.assertIn("volatility_index", metrics)

    def test_run_standalone_scenario_simulation(self):
        scenario_id = uuid.uuid4().hex
        base_multiplier = round(random.uniform(1.0, 5.0), 2)

        sim_result = {
            "scenario_id": scenario_id,
            "multiplier": base_multiplier,
            "stress_impact": random.uniform(-0.5, -0.05)
        }

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.run_scenario_simulation") as mock_run_sim:
            mock_run_sim.return_value = sim_result

            result = self.engine.run_standalone_scenario_simulation(
                scenario_id=scenario_id,
                base_multiplier=base_multiplier
            )

            self.assertEqual(result, sim_result)
            self.assertEqual(result["scenario_id"], scenario_id)

    def test_forecast_portfolio_stress_volatility_wrapper(self):
        portfolio_id = uuid.uuid4().hex
        scenario_data = {uuid.uuid4().hex: random.randint(1, 100)}
        monte_carlo_metrics = {uuid.uuid4().hex: random.random()}
        confidence_level = round(random.uniform(0.90, 0.99), 2)

        expected_forecast = {
            "portfolio_id": portfolio_id,
            "forecasted_var": random.uniform(1000, 10000)
        }

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.forecast_portfolio_stress_volatility") as mock_forecast:
            mock_forecast.return_value = expected_forecast

            res = self.engine.forecast_portfolio_stress_volatility_wrapper(
                portfolio_id=portfolio_id,
                scenario_data=scenario_data,
                monte_carlo_metrics=monte_carlo_metrics,
                confidence_level=confidence_level
            )

            self.assertEqual(res, expected_forecast)

    def test_engine_raises_var_error_on_general_failure(self):
        portfolio_id = uuid.uuid4().hex
        scenario_code = uuid.uuid4().hex

        with patch("skills.market_portfolio_predictive_var_engine.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2") as mock_forecaster_cls:
            instance_forecaster = mock_forecaster_cls.return_value
            instance_forecaster.forecast_volatility.side_effect = RuntimeError("Critical System Failure")

            with self.assertRaises(VarEngineError):
                self.engine.calculate_predictive_var(
                    portfolio_id=portfolio_id,
                    scenario_code=scenario_code,
                    simulations=100,
                    horizon_days=5,
                    confidence_level=0.95
                )

if __name__ == "__main__":
    unittest.main()