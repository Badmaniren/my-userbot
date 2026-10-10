import unittest
from unittest.mock import patch
import random
import uuid
import math
import io

from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine,
    MarketPortfolioPredictiveVarEngine,
    VarEngineError,
    InsufficientDataError,
    calculate_predictive_stress_var,
)


class TestPredictiveVarEngine(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.scenario_code = uuid.uuid4().hex
        self.simulations = random.randint(100, 2000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.8, 0.99), 2)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.engine = PredictiveVarEngine()

    def test_init_defaults(self):
        eng = PredictiveVarEngine()
        self.assertIsNone(eng.db_storage)
        self.assertIsNone(eng.extractor_tool)
        self.assertIsNone(eng.market_anomaly_detector)
        self.assertIsNotNone(eng.forecaster)
        self.assertIsNotNone(eng.monte_carlo_engine)

    def test_calculate_predictive_var_success(self):
        simulated_losses_list = [round(random.uniform(100.0, 5000.0), 2) for _ in range(50)]
        vol_mock_data = {"volatility_score": random.uniform(0.1, 0.5), "id": self.portfolio_id}
        mc_mock_data = {"simulated_losses": simulated_losses_list}

        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", return_value=vol_mock_data) as m_vol, \
             patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.run_simulation", return_value=mc_mock_data) as m_mc:

            res = self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value
            )

            m_vol.assert_called_once_with(portfolio_id=self.portfolio_id, scenario_code=self.scenario_code)
            m_mc.assert_called_once()
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["scenario_code"], self.scenario_code)
            self.assertIn("var_value", res)
            self.assertIn("cvar_value", res)
            self.assertIsInstance(res["ml_volatility_metrics"], dict)
            self.assertIsInstance(res["monte_carlo_metrics"], dict)

    def test_calculate_predictive_var_iterations_override(self):
        iterations_val = random.randint(50, 500)
        vol_mock_data = {}
        mc_mock_data = {"simulated_losses": [10.0, 20.0, 30.0]}

        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", return_value=vol_mock_data), \
             patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.run_simulation", return_value=mc_mock_data) as m_mc:

            res = self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                iterations=iterations_val
            )
            self.assertEqual(res["simulations_run"], iterations_val)

    def test_calculate_predictive_var_invalid_values(self):
        with self.assertRaises(ValueError):
            self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=-100.0
            )

        with self.assertRaises(ValueError):
            self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                confidence_level=1.5
            )

        with self.assertRaises(ValueError):
            self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                confidence_level=0.0
            )

    def test_calculate_predictive_var_scenario_params_mapping(self):
        custom_scenario = uuid.uuid4().hex
        scenario_params = {"scenario_code": custom_scenario}
        vol_mock_data = {}
        mc_mock_data = {"simulated_losses": [5.0, 15.0]}

        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", return_value=vol_mock_data) as m_vol, \
             patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.run_simulation", return_value=mc_mock_data):

            self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                scenario_params=scenario_params
            )
            m_vol.assert_called_once_with(portfolio_id=self.portfolio_id, scenario_code=custom_scenario)

    def test_calculate_predictive_var_forecaster_runtime_error(self):
        err_msg = uuid.uuid4().hex
        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", side_effect=RuntimeError(err_msg)):
            with self.assertRaises(VarEngineError) as ctx:
                self.engine.calculate_predictive_var(portfolio_id=self.portfolio_id)
            self.assertIn(err_msg, str(ctx.exception))

    def test_calculate_predictive_var_forecaster_generic_error(self):
        err_msg = uuid.uuid4().hex
        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", side_effect=Exception(err_msg)):
            with self.assertRaises(InsufficientDataError) as ctx:
                self.engine.calculate_predictive_var(portfolio_id=self.portfolio_id)
            self.assertIn(err_msg, str(ctx.exception))

    def test_calculate_predictive_var_monte_carlo_error(self):
        err_msg = uuid.uuid4().hex
        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", return_value={}), \
             patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.run_simulation", side_effect=Exception(err_msg)):
            with self.assertRaises(VarEngineError) as ctx:
                self.engine.calculate_predictive_var(portfolio_id=self.portfolio_id)
            self.assertIn(err_msg, str(ctx.exception))

    def test_calculate_predictive_var_empty_losses(self):
        vol_mock_data = {}
        mc_mock_data = {"simulated_losses": []}
        with patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.forecast_volatility", return_value=vol_mock_data), \
             patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.run_simulation", return_value=mc_mock_data):
            res = self.engine.calculate_predictive_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value
            )
            self.assertEqual(res["var_value"], 0.0)
            self.assertEqual(res["cvar_value"], 0.0)

    def test_delegated_methods(self):
        stream_mock = io.BytesIO(uuid.uuid4().bytes)
        soup_content = uuid.uuid4().hex
        report_id = uuid.uuid4().hex
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        target_url = f"https://{uuid.uuid4().hex}.com/api"
        scenario_id = uuid.uuid4().hex
        base_multiplier = round(random.uniform(1.0, 5.0), 2)

        with patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.consume_stream", return_value={"status": "consumed"}) as m1, \
             patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.evaluate_stress_anomaly", return_value={"anomaly": False}) as m2, \
             patch("skills.market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine.export_report", return_value={"exported": True}) as m3, \
             patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2.fetch_external_ml_metrics", return_value={"metric": 123}) as m4, \
             patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.run_scenario_simulation", return_value={"sim": True}) as m5, \
             patch("skills.market_portfolio_stress_ml_volatility_forecaster_v2.forecast_portfolio_stress_volatility", return_value={"vol": True}) as m6:

            self.assertEqual(self.engine.process_market_stream(stream_mock), {"status": "consumed"})
            m1.assert_called_once_with(stream_mock)

            self.assertEqual(self.engine.evaluate_risk_anomaly(self.portfolio_id, self.scenario_code, soup_content), {"anomaly": False})
            m2.assert_called_once_with(portfolio_id=self.portfolio_id, scenario_code=self.scenario_code, soup_content=soup_content)

            self.assertEqual(self.engine.export_predictive_audit_report(report_id, loss_limit), {"exported": True})
            m3.assert_called_once_with(report_id=report_id, loss_limit=loss_limit)

            self.assertEqual(self.engine.fetch_external_predictive_metrics(target_url, self.portfolio_id, self.scenario_code), {"metric": 123})
            m4.assert_called_once_with(target_url=target_url, portfolio_id=self.portfolio_id, scenario_code=self.scenario_code)

            self.assertEqual(self.engine.run_standalone_scenario_simulation(scenario_id, base_multiplier), {"sim": True})
            m5.assert_called_once_with(scenario_id=scenario_id, base_multiplier=base_multiplier)

            scenario_data = {"test": True}
            monte_carlo_metrics = {"mc": True}
            self.assertEqual(self.engine.forecast_portfolio_stress_volatility_wrapper(self.portfolio_id, scenario_data, monte_carlo_metrics, self.confidence_level), {"vol": True})
            m6.assert_called_once_with(portfolio_id=self.portfolio_id, scenario_data=scenario_data, monte_carlo_metrics=monte_carlo_metrics, confidence_level=self.confidence_level)

    def test_calculate_predictive_stress_var_wrapper(self):
        scenario_params = {"param": uuid.uuid4().hex}
        with patch("skills.market_portfolio_predictive_var_engine.calculate_predictive_stress_var", return_value={"wrapped": True}) as m_calc:
            res = self.engine.calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.simulations
            )
            self.assertEqual(res, {"wrapped": True})
            m_calc.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.simulations
            )

    def test_market_portfolio_predictive_var_engine_alias(self):
        alias_engine = MarketPortfolioPredictiveVarEngine()
        self.assertIsInstance(alias_engine, PredictiveVarEngine)


class TestCalculatePredictiveStressVarStandalone(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.portfolio_value = round(random.uniform(50000.0, 500000.0), 2)
        self.scenario_params = {"macro_shock": round(random.uniform(0.05, 0.3), 2)}
        self.confidence_level = round(random.uniform(0.85, 0.99), 2)
        self.horizon_days = random.randint(1, 15)
        self.iterations = random.randint(100, 1000)

    def test_validation_errors(self):
        with self.assertRaises(ValueError):
            calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=-10.0,
                scenario_params=self.scenario_params
            )

        with self.assertRaises(ValueError):
            calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=1.1
            )

    def test_forecast_and_mc_success_with_candidates(self):
        ml_mock = {"ml_score": random.uniform(0.1, 0.9)}
        mc_mock = {"stress_var": round(random.uniform(100.0, 1000.0), 2), "conditional_var": round(random.uniform(1100.0, 2000.0), 2)}

        with patch("skills.market_portfolio_predictive_var_engine.forecast_portfolio_stress_volatility", return_value=ml_mock) as m_forecast, \
             patch("skills.market_portfolio_predictive_var_engine.run_monte_carlo_stress_test", return_value=mc_mock) as m_run_mc:

            res = calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.iterations
            )

            m_forecast.assert_called_once()
            m_run_mc.assert_called_once()
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["portfolio_value"], self.portfolio_value)
            self.assertEqual(res["ml_volatility_metrics"], ml_mock)
            self.assertEqual(res["monte_carlo_metrics"], mc_mock)
            self.assertIn("stress_var", res)
            self.assertIn("conditional_var", res)

    def test_forecast_typeerror_fallbacks(self):
        ml_mock = {"fallback": True}
        mc_mock = {"var_value": 500.0, "cvar_value": 600.0}

        def mock_forecast_side_effect(*args, **kwargs):
            if "monte_carlo_metrics" in kwargs:
                raise TypeError("No such argument")
            if "confidence_level" in kwargs:
                raise TypeError("No such argument")
            return ml_mock

        with patch("skills.market_portfolio_predictive_var_engine.forecast_portfolio_stress_volatility", side_effect=mock_forecast_side_effect), \
             patch("skills.market_portfolio_predictive_var_engine.run_monte_carlo_stress_test", return_value=mc_mock):

            res = calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.iterations
            )
            self.assertEqual(res["ml_volatility_metrics"], ml_mock)

    def test_run_monte_carlo_typeerror_fallbacks(self):
        ml_mock = {}
        mc_mock = {"stress_var": 400.0}

        def mock_mc_side_effect(*args, **kwargs):
            if "volatility_metrics" in kwargs:
                raise TypeError("No vol metrics")
            if "horizon_days" in kwargs and "iterations" in kwargs:
                raise TypeError("No horizon")
            if "iterations" in kwargs:
                raise TypeError("No iterations")
            return mc_mock

        with patch("skills.market_portfolio_predictive_var_engine.forecast_portfolio_stress_volatility", return_value=ml_mock), \
             patch("skills.market_portfolio_predictive_var_engine.run_monte_carlo_stress_test", side_effect=mock_mc_side_effect):

            res = calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.iterations
            )
            self.assertEqual(res["monte_carlo_metrics"], mc_mock)

    def test_fallback_when_var_candidate_is_none(self):
        ml_mock = {}
        mc_mock = {}  # No stress_var or var_value

        with patch("skills.market_portfolio_predictive_var_engine.forecast_portfolio_stress_volatility", return_value=ml_mock), \
             patch("skills.market_portfolio_predictive_var_engine.run_monte_carlo_stress_test", return_value=mc_mock):

            res = calculate_predictive_stress_var(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.iterations
            )

            self.assertIsNotNone(res["stress_var"])
            self.assertIsNotNone(res["conditional_var"])
            self.assertLessEqual(res["stress_var"], self.portfolio_value)
            self.assertGreaterEqual(res["conditional_var"], res["stress_var"])


if __name__ == "__main__":
    unittest.main()