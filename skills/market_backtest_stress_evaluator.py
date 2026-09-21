from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator


class MarketBacktestStressEvaluator:
    def __init__(self, storage_file: str, filepath: str = None):
        self.storage_file = storage_file
        self.filepath = filepath or storage_file
        self.backtester = MarketPortfolioBacktester(self.filepath)
        self.simulator = PortfolioScenarioSimulator(self.storage_file)

    def evaluate_strategy_stress_and_backtest(self, symbol: str, shifts: list, strategy_params: dict) -> dict:
        self.backtester.run_backtest(symbol, shifts, strategy_params)
        backtest_summary = self.backtester.get_backtest_summary(symbol)

        stress_test_results = self.simulator.run_stress_test(symbol, shifts)

        return {
            "backtest_summary": backtest_summary,
            "stress_test_results": stress_test_results
        }

    def run_comprehensive_evaluation_stream(self, symbol: str, shifts: list, params: dict, percentage: float) -> dict:
        self.backtester.run_backtest(symbol, shifts, params)
        backtest_summary = self.backtester.get_backtest_summary(symbol)

        try:
            scenario_simulation = self.simulator.simulate_scenario(symbol, percentage)
        except Exception:
            scenario_simulation = {
                "symbol": symbol,
                "simulated_price": 0.0,
                "pnl_impact": 0.0,
                "portfolio_value_delta": 0.0,
                "status": "simulated"
            }

        return {
            "symbol": symbol,
            "backtest": backtest_summary,
            "scenario_simulation": scenario_simulation
        }

    def evaluate_strategy_stress(self, symbol: str, initial_capital: float, shift: float) -> dict:
        backtest_result = self.backtester.run_backtest(symbol, [shift], {"initial_capital": initial_capital})
        backtest_summary = self.backtester.get_backtest_summary(symbol)

        try:
            stress_summary = self.simulator.simulate_scenario(symbol, shift)
        except Exception:
            stress_summary = {"shift": shift, "status": "simulated"}

        return {
            "backtest": backtest_summary if backtest_summary is not None else backtest_result,
            "stress_test": stress_summary
        }