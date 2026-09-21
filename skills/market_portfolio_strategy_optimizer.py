from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class PortfolioStrategyOptimizer:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.backtester = MarketPortfolioBacktester(storage_file)
        self.simulator = PortfolioScenarioSimulator(storage_file)

    def optimize_strategy(self, symbol: str, shifts, percentage: float) -> dict:
        backtest_result = self.backtester.run_backtest(symbol, shifts)
        simulation_result = self.simulator.simulate_scenario(symbol, percentage)
        return {
            'backtest': backtest_result,
            'simulation': simulation_result
        }

    def evaluate_resilience(self, symbol: str, shifts) -> dict:
        stress_data = self.simulator.run_stress_test(symbol, shifts)
        drawdown_checked = self.backtester.calculate_maximum_drawdown(symbol)
        return {
            'stress_data': stress_data,
            'drawdown_checked': drawdown_checked
        }

    def load_strategy_stream(self, filepath: str):
        with open(filepath, 'rb') as f:
            return f.read()

    def optimize_and_evaluate(self, symbol: str, allocation: float, shifts) -> dict:
        if isinstance(shifts, (float, int)):
            shifts_iterable = [shifts]
        else:
            shifts_iterable = shifts

        backtest_res = self.backtester.run_backtest(symbol, shifts_iterable)
        stress_res = self.simulator.run_stress_test(symbol, shifts_iterable)
        
        try:
            drawdown = self.backtester.calculate_maximum_drawdown(symbol)
            if isinstance(drawdown, str):
                drawdown = float(drawdown)
        except Exception:
            drawdown = 0.0

        optimized_weights = {symbol: allocation}
        resilience_score = 1.0 - abs(drawdown) if drawdown is not None else 0.5
        
        return {
            "optimized_weights": optimized_weights,
            "resilience_score": resilience_score,
            "backtest": backtest_res,
            "stress": stress_res
        }

    def get_strategy_summary(self, symbol: str) -> dict:
        return {
            symbol: {
                "summary": "active",
                "storage": self.storage_file
            }
        }