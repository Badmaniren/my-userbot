from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics

class MarketPortfolioBacktestEvaluatorBridge:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.backtester = MarketPortfolioBacktester(self.storage_file)
        self.analytics = PortfolioPerformanceAnalytics(self.storage_file)

    def evaluate_backtest_performance(self, symbol: str) -> dict:
        backtest_summary = self.backtester.get_backtest_summary(symbol)
        performance_metrics = self.analytics.calculate_metrics(symbol)
        performance_evaluation = self.analytics.evaluate_performance(symbol)

        return {
            "backtest_summary": backtest_summary,
            "performance_metrics": performance_metrics,
            "performance_evaluation": performance_evaluation
        }

    def run_comprehensive_evaluation(self, symbol: str, initial_capital_or_shifts, strategy_params: dict) -> dict:
        backtest_execution = self.backtester.run_backtest(symbol, initial_capital_or_shifts, strategy_params)
        summary = self.backtester.get_backtest_summary(symbol)
        metrics = self.analytics.calculate_metrics(symbol)
        evaluation = self.analytics.evaluate_performance(symbol)

        return {
            "backtest_execution": backtest_execution,
            "summary": summary,
            "metrics": metrics,
            "evaluation": evaluation
        }

    def evaluate_strategy_backtest(self, symbol: str, initial_capital: float, strategy_params: dict) -> dict:
        self.backtester.run_backtest(symbol, initial_capital, strategy_params)
        backtest_summary = self.backtester.get_backtest_summary(symbol)
        performance_metrics = self.analytics.calculate_metrics(symbol)
        performance_evaluation = self.analytics.evaluate_performance(symbol)

        return {
            "backtest_summary": backtest_summary,
            "performance_metrics": performance_metrics,
            "performance_evaluation": performance_evaluation
        }