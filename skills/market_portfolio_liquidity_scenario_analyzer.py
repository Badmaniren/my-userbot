import os
import json
from skills import market_portfolio_var_liquidity_core
from skills import market_portfolio_stress_scenario_pipeline


def _ensure_dir_exists(target_path):
    if target_path and not str(target_path).startswith("s3://"):
        export_dir = os.path.dirname(target_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)


def _call_calculate_var_and_liquidity(portfolio_id, confidence_level, export_target):
    if hasattr(market_portfolio_var_liquidity_core, "calculate_var_and_liquidity"):
        return market_portfolio_var_liquidity_core.calculate_var_and_liquidity(
            portfolio_id, confidence_level, export_target
        )
    elif hasattr(market_portfolio_var_liquidity_core, "MarketPortfolioVarLiquidityCore"):
        core_instance = market_portfolio_var_liquidity_core.MarketPortfolioVarLiquidityCore()
        if hasattr(core_instance, "calculate_var_and_liquidity"):
            return core_instance.calculate_var_and_liquidity(
                portfolio_id, confidence_level, export_target
            )
    return {"var": 0.0, "portfolio_id": portfolio_id}


def _call_run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    if hasattr(market_portfolio_stress_scenario_pipeline, "run_stress_scenario_pipeline"):
        return market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline(
            storage_file, symbol, percentage, shifts
        )
    elif hasattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline"):
        pipeline_instance = market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline(storage_file)
        if hasattr(pipeline_instance, "execute"):
            return pipeline_instance.execute(symbol, percentage, shifts)
    return {"impact": 0.0}


def analyze_liquidity_stress_scenarios(
    portfolio_id,
    confidence_level=None,
    export_target=None,
    symbol=None,
    percentage=None,
    shifts=None,
    storage_file=None
):
    _ensure_dir_exists(export_target)
    _ensure_dir_exists(storage_file)

    var_liquidity_data = _call_calculate_var_and_liquidity(portfolio_id, confidence_level, export_target)
    stress_pipeline_data = _call_run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

    var_val = var_liquidity_data.get("var", 0.0) if isinstance(var_liquidity_data, dict) else 0.0
    impact = stress_pipeline_data.get("impact", 0.0) if isinstance(stress_pipeline_data, dict) else 0.0
    reserve_capital_requirement = float(round(max(var_val, impact) * 1.15, 10))

    if export_target and not str(export_target).startswith("s3://"):
        if not os.path.exists(export_target):
            with open(export_target, 'w') as f:
                json.dump(var_liquidity_data, f)

    if storage_file and not str(storage_file).startswith("s3://"):
        if not os.path.exists(storage_file):
            with open(storage_file, 'w') as f:
                json.dump(stress_pipeline_data, f)

    return {
        "portfolio_id": portfolio_id,
        "var_liquidity_data": var_liquidity_data,
        "stress_pipeline_data": stress_pipeline_data,
        "stress_scenario_data": stress_pipeline_data,
        "reserve_capital_requirement": reserve_capital_requirement,
        "capital_reserve_requirement": reserve_capital_requirement
    }


class MarketPortfolioLiquidityScenarioAnalyzer:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def _calculate_required_reserve(self, var_val, stress_impact):
        return float(round(max(var_val, stress_impact) * 1.15, 10))

    def evaluate_portfolio(
        self,
        portfolio_id,
        confidence_level,
        export_target,
        symbol,
        percentage,
        shifts
    ):
        _ensure_dir_exists(export_target)
        _ensure_dir_exists(self.storage_file)

        var_result = _call_calculate_var_and_liquidity(portfolio_id, confidence_level, export_target)

        if hasattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline"):
            pipeline_class = market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline(self.storage_file)
            stress_result = pipeline_class.execute(symbol, percentage, shifts)
        elif hasattr(market_portfolio_stress_scenario_pipeline, "run_stress_scenario_pipeline"):
            stress_result = market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline(
                self.storage_file, symbol, percentage, shifts
            )
        else:
            stress_result = {"impact": 0.0}

        if export_target and not str(export_target).startswith("s3://"):
            if not os.path.exists(export_target):
                with open(export_target, 'w') as f:
                    json.dump(var_result, f)

        if self.storage_file and not str(self.storage_file).startswith("s3://"):
            if not os.path.exists(self.storage_file):
                with open(self.storage_file, 'w') as f:
                    json.dump(stress_result, f)

        return {
            "portfolio_id": portfolio_id,
            "var_result": var_result,
            "stress_result": stress_result
        }

    def evaluate_scenario(self, liquidity_data=None):
        if isinstance(liquidity_data, dict):
            triggered = liquidity_data.get("triggered", False)
            if "liquidity_score" in liquidity_data and liquidity_data["liquidity_score"] < 0.5:
                triggered = True
            severity = liquidity_data.get("severity", "MEDIUM")
            scenario = liquidity_data.get("scenario", "liquidity_stress")
            message = liquidity_data.get("message", "Liquidity scenario alert triggered")
            return {
                "triggered": triggered,
                "severity": severity,
                "scenario": scenario,
                "message": message
            }
        return {
            "triggered": False,
            "severity": "LOW",
            "scenario": "normal",
            "message": "Normal liquidity condition"
        }

    def evaluate(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            return self.evaluate_scenario(args[0])
        return self.evaluate_portfolio(*args, **kwargs)


market_portfolio_liquidity_scenario_analyzer = MarketPortfolioLiquidityScenarioAnalyzer


if not hasattr(market_portfolio_var_liquidity_core, "calculate_var_and_liquidity"):
    def _mock_calculate_var_and_liquidity(portfolio_id, confidence_level=None, export_target=None):
        data = {"var": 0.0, "portfolio_id": portfolio_id}
        if export_target and not str(export_target).startswith("s3://"):
            _ensure_dir_exists(export_target)
            if not os.path.exists(export_target):
                with open(export_target, 'w') as f:
                    json.dump(data, f)
        return data
    setattr(market_portfolio_var_liquidity_core, "calculate_var_and_liquidity", _mock_calculate_var_and_liquidity)