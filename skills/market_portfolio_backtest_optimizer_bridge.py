from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class PortfolioBacktestOptimizerBridge:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.backtester = MarketPortfolioBacktester(storage_file)
        self.optimizer = PortfolioStrategyOptimizer(storage_file)

    def run_bridge_pipeline(self, symbol: str, shifts: int, percentage: float) -> dict:
        optimizer_result = self.optimizer.optimize_strategy(
            symbol=symbol,
            shifts=shifts,
            percentage=percentage
        )

        equity_curve = self.backtester.run_backtest(
            symbol=symbol,
            initial_capital_or_shifts=shifts,
            strategy_params=optimizer_result
        )

        maximum_drawdown = self.backtester.calculate_maximum_drawdown(equity_curve)
        backtest_summary = self.backtester.get_backtest_summary(symbol)

        return {
            "optimizer_result": optimizer_result,
            "backtest_summary": backtest_summary,
            "maximum_drawdown": maximum_drawdown,
            "equity_curve": equity_curve
        }

    def evaluate_bridge_resilience(self, symbol: str, shifts: int) -> dict:
        return self.optimizer.evaluate_resilience(symbol, shifts)

    def simulate_bridge_historical_trades(self, symbol: str, allocation: float) -> list:
        return self.backtester.simulate_historical_trades(symbol, allocation)

    def optimize_and_backtest(self, symbol: str, shifts: int, percentage: float) -> dict:
        return self.run_bridge_pipeline(symbol, shifts, percentage)

MarketPortfolioBacktestOptimizerBridge = PortfolioBacktestOptimizerBridge