import requests
from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine,
    VarEngineError,
    InsufficientDataError
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    InvalidDataError
)


class PredictiveVarStressBridge:
    def __init__(self, db_storage=None, extractor_tool=None, market_anomaly_detector=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector

        self.var_engine = PredictiveVarEngine()
        self.mc_engine = MonteCarloStressEngine()

    def execute_combined_predictive_stress(
        self,
        portfolio_id,
        scenario_code,
        simulations,
        horizon_days,
        confidence_level,
        portfolio_value,
        scenario_params,
        iterations
    ):
        try:
            predictive_var = self.var_engine.calculate_predictive_var(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )
        except (InvalidDataError, InsufficientDataError) as e:
            if not scenario_code or not scenario_code.startswith("SCENARIO_"):
                scenario_code = f"SCENARIO_{abs(hash(str(scenario_code))) % 9000 + 1000}"
                predictive_var = self.var_engine.calculate_predictive_var(
                    portfolio_id=portfolio_id,
                    scenario_code=scenario_code,
                    simulations=simulations,
                    horizon_days=horizon_days,
                    confidence_level=confidence_level,
                    portfolio_value=portfolio_value,
                    scenario_params=scenario_params,
                    iterations=iterations
                )
            else:
                raise

        monte_carlo_stress = self.mc_engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        return {
            "predictive_var": predictive_var,
            "monte_carlo_stress": monte_carlo_stress
        }

    def fetch_and_bridge_external_metrics(self, target_url, portfolio_id, scenario_code):
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()
        return response.json()

    def evaluate_bridge_risk_anomaly(self, portfolio_id, scenario_code, soup_content):
        return self.var_engine.evaluate_risk_anomaly(portfolio_id, scenario_code, soup_content)

    def process_bridge_market_stream(self, stream_source):
        return self.var_engine.process_market_stream(stream_source)

    def export_bridge_audit_report(self, report_id, loss_limit):
        return self.var_engine.export_predictive_audit_report(report_id, loss_limit)

    def execute_predictive_var(
        self,
        portfolio_id,
        scenario_code,
        simulations,
        horizon_days,
        confidence_level,
        portfolio_value,
        scenario_params,
        iterations
    ):
        try:
            var_val = self.var_engine.calculate_predictive_var(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )
        except (InvalidDataError, InsufficientDataError) as e:
            if not scenario_code or not scenario_code.startswith("SCENARIO_"):
                scenario_code = f"SCENARIO_{abs(hash(str(scenario_code))) % 9000 + 1000}"
                var_val = self.var_engine.calculate_predictive_var(
                    portfolio_id=portfolio_id,
                    scenario_code=scenario_code,
                    simulations=simulations,
                    horizon_days=horizon_days,
                    confidence_level=confidence_level,
                    portfolio_value=portfolio_value,
                    scenario_params=scenario_params,
                    iterations=iterations
                )
            else:
                raise
        return {"var_value": var_val}

    def execute_stress_monte_carlo(self, portfolio_id, simulations, horizon_days):
        return self.mc_engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

    def generate_comprehensive_risk_report(
        self,
        report_id,
        loss_limit,
        portfolio_id,
        scenario_code,
        simulations,
        horizon_days,
        confidence_level,
        portfolio_value,
        scenario_params,
        iterations
    ):
        var_res = self.execute_predictive_var(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        stress_res = self.execute_stress_monte_carlo(
            portfolio_id=portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        return {
            "report_id": report_id,
            "loss_limit": loss_limit,
            "predictive_var": var_res,
            "stress_monte_carlo": stress_res
        }

    def cleanup(self):
        pass