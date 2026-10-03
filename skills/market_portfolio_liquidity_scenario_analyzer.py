import os
import json
from skills import market_portfolio_var_liquidity_core
from skills import market_portfolio_stress_scenario_pipeline

def analyze_liquidity_stress_scenarios(
    portfolio_id,
    confidence_level=None,
    export_target=None,
    symbol=None,
    percentage=None,
    shifts=None,
    storage_file=None
):
    if hasattr(market_portfolio_var_liquidity_core, "calculate_var_and_liquidity"):
        var_liquidity_data = market_portfolio_var_liquidity_core.calculate_var_and_liquidity(
            portfolio_id, confidence_level, export_target
        )
    else:
        core_instance = market_portfolio_var_liquidity_core.market_portfolio_var_liquidity_core()
        var_liquidity_data = core_instance.calculate_var_and_liquidity(
            portfolio_id, confidence_level, export_target
        )
    
    if hasattr(market_portfolio_stress_scenario_pipeline, "run_stress_scenario_pipeline"):
        stress_pipeline_data = market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline(
            storage_file, symbol, percentage, shifts
        )
    else:
        pipeline_instance = market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline(storage_file)
        stress_pipeline_data = pipeline_instance.execute(symbol, percentage, shifts)
    
    var_val = var_liquidity_data.get("var", 0.0)
    impact = stress_pipeline_data.get("impact", 0.0)
    reserve_capital_requirement = max(var_val, impact) * 1.15
    
    if export_target and not str(export_target).startswith("s3://"):
        export_dir = os.path.dirname(export_target)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        with open(export_target, 'w') as f:
            json.dump(var_liquidity_data, f)

    if storage_file:
        storage_dir = os.path.dirname(storage_file)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
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

def market_portfolio_liquidity_scenario_analyzer(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    elif isinstance(payload, str):
        payload = {"portfolio_id": payload}
    elif not isinstance(payload, dict):
        payload = {}

    portfolio_id = payload.get("portfolio_id", payload.get("report_id", "default_portfolio"))
    confidence_level = payload.get("confidence_level", 0.95)
    export_target = payload.get("export_target")
    symbol = payload.get("symbol", "AAPL")
    percentage = payload.get("percentage", 0.0)
    shifts = payload.get("shifts", [0.0])
    storage_file = payload.get("storage_file", "default_scenario_storage.json")

    return analyze_liquidity_stress_scenarios(
        portfolio_id=portfolio_id,
        confidence_level=confidence_level,
        export_target=export_target,
        symbol=symbol,
        percentage=percentage,
        shifts=shifts,
        storage_file=storage_file
    )


class MarketPortfolioLiquidityScenarioAnalyzer:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def _calculate_required_reserve(self, var_val, stress_impact):
        return max(var_val, stress_impact) * 1.15

    def evaluate_portfolio(
        self,
        portfolio_id,
        confidence_level,
        export_target,
        symbol,
        percentage,
        shifts
    ):
        if hasattr(market_portfolio_var_liquidity_core, "market_portfolio_var_liquidity_core"):
            core_module = market_portfolio_var_liquidity_core.market_portfolio_var_liquidity_core()
            var_result = core_module.calculate_var_and_liquidity(portfolio_id, confidence_level, export_target)
        else:
            var_result = market_portfolio_var_liquidity_core.calculate_var_and_liquidity(
                portfolio_id, confidence_level, export_target
            )
        
        if hasattr(market_portfolio_stress_scenario_pipeline, "PortfolioStressScenarioPipeline"):
            pipeline_class = market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline(self.storage_file)
            stress_result = pipeline_class.execute(symbol, percentage, shifts)
        else:
            stress_result = market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline(
                self.storage_file, symbol, percentage, shifts
            )
        
        return {
            "portfolio_id": portfolio_id,
            "var_result": var_result,
            "stress_result": stress_result
        }