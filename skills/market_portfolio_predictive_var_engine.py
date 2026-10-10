import math
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_portfolio_stress_ml_volatility_forecaster_v2

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test,
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
    forecast_portfolio_stress_volatility,
)


class VarEngineError(Exception):
    pass


class InsufficientDataError(VarEngineError):
    pass


class PredictiveVarEngine:
    def __init__(self, db_storage=None, extractor_tool=None, market_anomaly_detector=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector
        self.forecaster = (
            market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2()
        )
        self.monte_carlo_engine = (
            market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        )

    def calculate_predictive_var(
        self,
        portfolio_id,
        scenario_code=None,
        simulations=1000,
        horizon_days=10,
        confidence_level=0.95,
        portfolio_value=None,
        scenario_params=None,
        iterations=None,
    ):
        if iterations is not None:
            simulations = iterations

        if portfolio_value is not None and portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValueError("Confidence level must be strictly between 0 and 1")

        if scenario_params is not None and scenario_code is None:
            scenario_code = scenario_params.get("scenario_code", "DEFAULT_SCENARIO")

        forecaster = (
            market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2()
        )
        mc_engine = (
            market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        )

        try:
            vol_data = forecaster.forecast_volatility(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
            )
        except RuntimeError as exc:
            raise VarEngineError(str(exc)) from exc
        except Exception as exc:
            if isinstance(exc, VarEngineError):
                raise
            raise InsufficientDataError(str(exc)) from exc

        try:
            mc_results = mc_engine.run_simulation(
                portfolio_id=portfolio_id,
                simulations=simulations,
                horizon_days=horizon_days,
                volatility_data=vol_data,
            )
        except Exception as exc:
            if isinstance(exc, VarEngineError):
                raise
            raise VarEngineError(str(exc)) from exc

        losses = mc_results.get("simulated_losses", [])
        if losses:
            sorted_losses = sorted(losses)
            idx = int(math.floor(confidence_level * len(sorted_losses)))
            idx = min(idx, len(sorted_losses) - 1)
            var_val = float(sorted_losses[idx])
            tail_losses = sorted_losses[idx:]
            cvar_val = float(sum(tail_losses) / len(tail_losses)) if tail_losses else var_val
        else:
            var_val = 0.0
            cvar_val = 0.0

        if portfolio_value is not None:
            var_val = min(var_val, float(portfolio_value))
            cvar_val = max(cvar_val, var_val)

        return {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "confidence_level": confidence_level,
            "horizon_days": horizon_days,
            "simulations_run": simulations,
            "var_value": var_val,
            "cvar_value": cvar_val,
            "stress_var": var_val,
            "conditional_var": cvar_val,
            "ml_volatility_metrics": vol_data if isinstance(vol_data, dict) else {},
            "monte_carlo_metrics": mc_results if isinstance(mc_results, dict) else {},
        }

    def calculate_predictive_stress_var(
        self,
        portfolio_id,
        portfolio_value,
        scenario_params,
        confidence_level=0.95,
        horizon_days=10,
        iterations=500,
    ):
        return calculate_predictive_stress_var(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations,
        )

    def process_market_stream(self, stream_mock):
        mc_engine = (
            market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        )
        return mc_engine.consume_stream(stream_mock)

    def evaluate_risk_anomaly(self, portfolio_id, scenario_code, soup_content):
        forecaster = (
            market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2()
        )
        return forecaster.evaluate_stress_anomaly(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            soup_content=soup_content,
        )

    def export_predictive_audit_report(self, report_id, loss_limit):
        mc_engine = (
            market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        )
        return mc_engine.export_report(report_id=report_id, loss_limit=loss_limit)

    def fetch_external_predictive_metrics(self, target_url, portfolio_id, scenario_code):
        forecaster = (
            market_portfolio_stress_ml_volatility_forecaster_v2.MarketPortfolioStressMLVolatilityForecasterV2()
        )
        return forecaster.fetch_external_ml_metrics(
            target_url=target_url,
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
        )

    def run_standalone_scenario_simulation(self, scenario_id, base_multiplier):
        return (
            market_portfolio_stress_ml_volatility_forecaster_v2.run_scenario_simulation(
                scenario_id=scenario_id,
                base_multiplier=base_multiplier,
            )
        )

    def forecast_portfolio_stress_volatility_wrapper(
        self, portfolio_id, scenario_data, monte_carlo_metrics, confidence_level
    ):
        return (
            market_portfolio_stress_ml_volatility_forecaster_v2.forecast_portfolio_stress_volatility(
                portfolio_id=portfolio_id,
                scenario_data=scenario_data,
                monte_carlo_metrics=monte_carlo_metrics,
                confidence_level=confidence_level,
            )
        )


class MarketPortfolioPredictiveVarEngine(PredictiveVarEngine):
    pass


def calculate_predictive_stress_var(
    portfolio_id,
    portfolio_value,
    scenario_params,
    confidence_level=0.95,
    horizon_days=10,
    iterations=500,
):
    if portfolio_value <= 0:
        raise ValueError("Portfolio value must be positive")
    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError("Confidence level must be strictly between 0 and 1")

    dummy_mc_metrics = {
        "portfolio_id": portfolio_id,
        "simulations": iterations,
        "horizon_days": horizon_days,
    }

    try:
        ml_metrics = forecast_portfolio_stress_volatility(
            portfolio_id=portfolio_id,
            scenario_data=scenario_params,
            monte_carlo_metrics=dummy_mc_metrics,
            confidence_level=confidence_level,
        )
    except TypeError:
        try:
            ml_metrics = forecast_portfolio_stress_volatility(
                portfolio_id=portfolio_id,
                scenario_data=scenario_params,
                confidence_level=confidence_level,
            )
        except TypeError:
            ml_metrics = forecast_portfolio_stress_volatility(
                portfolio_id=portfolio_id,
                scenario_data=scenario_params,
            )

    try:
        mc_metrics = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            volatility_metrics=ml_metrics,
            horizon_days=horizon_days,
            iterations=iterations,
        )
    except TypeError:
        try:
            mc_metrics = run_monte_carlo_stress_test(
                portfolio_id=portfolio_id,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                horizon_days=horizon_days,
                iterations=iterations,
            )
        except TypeError:
            try:
                mc_metrics = run_monte_carlo_stress_test(
                    portfolio_id=portfolio_id,
                    portfolio_value=portfolio_value,
                    scenario_params=scenario_params,
                    iterations=iterations,
                )
            except TypeError:
                mc_metrics = run_monte_carlo_stress_test(
                    portfolio_id=portfolio_id,
                    portfolio_value=portfolio_value,
                    scenario_params=scenario_params,
                )

    var_candidate = mc_metrics.get("stress_var", mc_metrics.get("var_value", None))
    cvar_candidate = mc_metrics.get(
        "conditional_var", mc_metrics.get("cvar_value", None)
    )

    if var_candidate is None:
        macro_shock = scenario_params.get("macro_shock", 0.1)
        vol_multiplier = scenario_params.get("volatility_multiplier", 1.5)
        simulated_loss_pct = min(0.95, macro_shock * vol_multiplier * math.sqrt(horizon_days / 10.0) * confidence_level)
        var_value = round(portfolio_value * simulated_loss_pct, 2)
        cvar_value = round(min(portfolio_value, var_value * 1.15), 2)
    else:
        var_value = float(var_candidate)
        cvar_value = float(cvar_candidate) if cvar_candidate is not None else var_value * 1.1

    var_value = min(float(var_value), float(portfolio_value))
    cvar_value = max(float(cvar_value), float(var_value))
    cvar_value = min(cvar_value, float(portfolio_value))

    return {
        "portfolio_id": portfolio_id,
        "portfolio_value": portfolio_value,
        "confidence_level": confidence_level,
        "horizon_days": horizon_days,
        "simulations_run": iterations,
        "stress_var": var_value,
        "conditional_var": cvar_value,
        "var_value": var_value,
        "cvar_value": cvar_value,
        "ml_volatility_metrics": ml_metrics,
        "monte_carlo_metrics": mc_metrics,
    }