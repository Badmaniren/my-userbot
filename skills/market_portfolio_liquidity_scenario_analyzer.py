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
    var_liquidity_data = market_portfolio_var_liquidity_core.calculate_var_and_liquidity(
        portfolio_id, confidence_level, export_target
    )
    
    stress_pipeline_data = market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline(
        storage_file, symbol, percentage, shifts
    )
    
    var_val = var_liquidity_data.get("var", 0.0)
    impact = stress_pipeline_data.get("impact", 0.0)
    reserve_capital_requirement = max(var_val, impact) * 1.15
    
    if export_target and not os.path.exists(export_target):
        with open(export_target, 'w') as f:
            json.dump(var_liquidity_data, f)

    if storage_file and not os.path.exists(storage_file):
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
        core_module = market_portfolio_var_liquidity_core.market_portfolio_var_liquidity_core()
        var_result = core_module.calculate_var_and_liquidity(portfolio_id, confidence_level, export_target)
        
        pipeline_class = market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline(self.storage_file)
        stress_result = pipeline_class.execute(symbol, percentage, shifts)
        
        return {
            "portfolio_id": portfolio_id,
            "var_result": var_result,
            "stress_result": stress_result
        }