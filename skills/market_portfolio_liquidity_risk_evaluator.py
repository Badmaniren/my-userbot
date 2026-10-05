import os
import json
from skills.market_portfolio_liquidity_scenario_analyzer import MarketPortfolioLiquidityScenarioAnalyzer
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core

class MarketPortfolioLiquidityRiskEvaluator:
    def __init__(self, storage_file: str = None):
        self.storage_file = storage_file

    def evaluate_comprehensive_risk(
        self,
        portfolio_id: str,
        confidence_level: float,
        export_target: str,
        symbol: str,
        percentage: float,
        shifts: list
    ) -> dict:
        analyzer = MarketPortfolioLiquidityScenarioAnalyzer(self.storage_file)
        scenario_output = analyzer.evaluate_portfolio(
            portfolio_id,
            confidence_level,
            export_target,
            symbol,
            percentage,
            shifts
        )

        var_instance = market_portfolio_var_liquidity_core()
        var_output = var_instance.calculate_var_and_liquidity(
            portfolio_id,
            confidence_level,
            export_target
        )

        return {
            "evaluated_portfolio": portfolio_id,
            "scenario_output": scenario_output,
            "var_output": var_output
        }


def evaluate_liquidity_risk(
    portfolio_id: str,
    confidence_level: float,
    export_target: str,
    symbol: str,
    percentage: float,
    shifts: list,
    storage_file: str = None
) -> dict:
    analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file)
    scenario_analysis = analyzer.evaluate_portfolio(
        portfolio_id,
        confidence_level,
        export_target,
        symbol,
        percentage,
        shifts
    )

    var_instance = market_portfolio_var_liquidity_core()
    var_liquidity_calculation = var_instance.calculate_var_and_liquidity(
        portfolio_id,
        confidence_level,
        export_target
    )

    return {
        "portfolio_id": portfolio_id,
        "scenario_analysis": scenario_analysis,
        "var_liquidity_calculation": var_liquidity_calculation
    }


def evaluate_liquidity_risk_assessment(
    portfolio_id: str,
    confidence_level: float,
    export_target: str,
    symbol: str,
    percentage: float,
    shifts: list,
    storage_file: str = None
) -> dict:
    file_existed = os.path.exists(export_target) if export_target else True

    analyzer = MarketPortfolioLiquidityScenarioAnalyzer(storage_file)
    scenario_analysis = analyzer.evaluate_portfolio(
        portfolio_id,
        confidence_level,
        export_target,
        symbol,
        percentage,
        shifts
    )

    var_instance = market_portfolio_var_liquidity_core()
    var_liquidity_core = var_instance.calculate_var_and_liquidity(
        portfolio_id,
        confidence_level,
        export_target
    )

    report_data = {
        "portfolio_id": portfolio_id,
        "scenario_analysis": scenario_analysis,
        "var_liquidity_core": var_liquidity_core
    }

    if isinstance(scenario_analysis, dict):
        report_data.update(scenario_analysis)
    if isinstance(var_liquidity_core, dict):
        report_data.update(var_liquidity_core)

    if export_target and not file_existed:
        with open(export_target, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)

    return report_data
