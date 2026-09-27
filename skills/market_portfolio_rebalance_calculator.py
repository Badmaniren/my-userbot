from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class PortfolioRebalanceCalculator:
    def __init__(self, storage_or_analytics, optimizer=None):
        if isinstance(storage_or_analytics, str):
            self.storage_file = storage_or_analytics
            self.analytics = PortfolioPerformanceAnalytics(self.storage_file)
            self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        else:
            self.analytics = storage_or_analytics
            self.optimizer = optimizer if optimizer is not None else PortfolioStrategyOptimizer(None)

    def calculate_rebalance(self, symbol, shifts, percentage):
        metrics = self.analytics.calculate_metrics(symbol)
        try:
            opt_strategy = self.optimizer.optimize_strategy(symbol, shifts, percentage)
        except (KeyError, TypeError):
            opt_strategy = {}

        target_weights = {symbol: percentage}
        deviations = {symbol: shifts}

        return {
            "target_weights": target_weights,
            "deviations": deviations,
            "metrics": metrics,
            "strategy": opt_strategy
        }

    def evaluate_rebalance_strategy(self, symbol, shifts):
        perf_eval = self.analytics.evaluate_performance(symbol)
        try:
            resilience_eval = self.optimizer.evaluate_resilience(symbol, shifts)
        except (KeyError, TypeError):
            resilience_eval = {}
        return {
            "symbol": symbol,
            "performance_evaluation": perf_eval,
            "resilience_evaluation": resilience_eval
        }

    def analyze_stream_and_summary(self, filepath, symbol):
        try:
            stream_data = self.optimizer.load_strategy_stream(filepath)
        except (FileNotFoundError, IOError, TypeError):
            stream_data = []

        try:
            summary = self.optimizer.get_strategy_summary(symbol)
        except (KeyError, TypeError):
            summary = {}

        return {
            "stream_data": stream_data,
            "summary": summary
        }

    def full_rebalance_cycle(self, symbol, allocation, shifts):
        try:
            opt_eval = self.optimizer.optimize_and_evaluate(symbol, allocation, shifts)
        except (KeyError, TypeError):
            opt_eval = {}
        return opt_eval