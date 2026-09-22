from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_backtester import MarketPortfolioBacktester


class PortfolioStrategyBacktestSync:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.optimizer = PortfolioStrategyOptimizer(storage_file)
        self.backtester = MarketPortfolioBacktester(storage_file)

    def sync_strategy_params(self, symbol: str, shifts=None, percentage: float = 0.0) -> dict:
        if shifts is None:
            shifts = [1, 5, 10]

        optimization_result = self.optimizer.optimize_strategy(symbol, shifts, percentage)
        backtest_result = self.backtester.run_backtest(symbol, shifts)
        resilience_result = self.optimizer.evaluate_resilience(symbol, shifts)

        synchronized_params = {
            "symbol": symbol,
            "optimal_shifts": shifts,
            "target_percentage": percentage,
            "resilience": resilience_result
        }

        return {
            "status": "synchronized",
            "symbol": symbol,
            "optimization": optimization_result,
            "backtest": backtest_result,
            "resilience": resilience_result,
            "synchronized_params": synchronized_params
        }

    def evaluate_and_sync(self, symbol: str, shifts=None, percentage: float = 0.0) -> dict:
        if shifts is None:
            shifts = [1, 5, 10]

        sync_data = self.sync_strategy_params(symbol, shifts, percentage)
        resilience_data = self.optimizer.evaluate_resilience(symbol, shifts)

        return {
            "sync_status": sync_data.get("status"),
            "resilience": resilience_data,
            "sync_details": sync_data
        }

    def export_sync_dump(self, filepath: str) -> bytes:
        with open(filepath, "rb") as f:
            return f.read()


def run_strategy_backtest_sync(storage_file: str, symbol: str, shifts=None, percentage: float = 0.0) -> dict:
    syncer = PortfolioStrategyBacktestSync(storage_file)
    return syncer.sync_strategy_params(symbol, shifts, percentage)
