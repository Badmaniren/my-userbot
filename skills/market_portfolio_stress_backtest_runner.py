from typing import Any, Dict, Optional
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class MarketPortfolioStressBacktestRunner:
    def __init__(self, filepath: Optional[str] = None) -> None:
        self.filepath = filepath
        self.backtester = MarketPortfolioBacktester(filepath=filepath)
        self.stress_pipeline = PortfolioStressScenarioPipeline(storage_file=filepath)

    def run_stress_backtest(
        self,
        symbol: str,
        initial_capital: float,
        strategy_params: Optional[Dict[str, Any]] = None,
        percentage: float = 0.0,
        shifts: Any = 0,
    ) -> Dict[str, Any]:
        if strategy_params is None:
            strategy_params = {}

        if self.filepath:
            self.backtester.load_data(self.filepath)

        stress_result = self.stress_pipeline.execute(
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.backtester.run_backtest(
            symbol=symbol,
            initial_capital_or_shifts=initial_capital,
            strategy_params=strategy_params
        )

        summary = self.backtester.get_backtest_summary(symbol)

        return {
            "symbol": symbol,
            "backtest_summary": summary,
            "stress_scenario_result": stress_result,
            "stress_results": stress_result,
            "validation_report": {
                "symbol": symbol,
                "backtest_summary": summary,
                "stress_scenario_result": stress_result
            }
        }


class MarketPortfolioStressBacktester(MarketPortfolioStressBacktestRunner):
    def run_complete_pipeline(
        self,
        symbol: str,
        percentage: float,
        shifts: Any,
        initial_capital: float,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = self.run_stress_backtest(
            symbol=symbol,
            initial_capital=initial_capital,
            strategy_params=strategy_params,
            percentage=percentage,
            shifts=shifts
        )
        result["status"] = "SUCCESS"
        return result


def run_stress_backtest_pipeline(
    filepath: Optional[str] = None,
    storage_file: Optional[str] = None,
    symbol: str = "",
    initial_capital: float = 0.0,
    strategy_params: Optional[Dict[str, Any]] = None,
    percentage: float = 0.0,
    shifts: Any = 0
) -> Dict[str, Any]:
    active_path = filepath if filepath is not None else storage_file
    runner = MarketPortfolioStressBacktestRunner(filepath=active_path)
    return runner.run_stress_backtest(
        symbol=symbol,
        initial_capital=initial_capital,
        strategy_params=strategy_params,
        percentage=percentage,
        shifts=shifts
    )