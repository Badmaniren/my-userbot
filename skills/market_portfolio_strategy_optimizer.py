from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class PortfolioStrategyOptimizer:
    def __init__(self, storage_file: str = "default.db"):
        self.storage_file = storage_file
        self.backtester = MarketPortfolioBacktester(storage_file)
        self.simulator = PortfolioScenarioSimulator(storage_file)

    def _validate_allocation(self, allocation: float) -> float:
        """Жесткая валидация весов активов и корректная обработка граничных условий."""
        if not isinstance(allocation, (int, float)):
            try:
                allocation = float(allocation)
            except (ValueError, TypeError):
                allocation = 0.0
        
        if allocation < 0.0:
            return 0.0
        if allocation > 1.0:
            return 1.0
        return float(allocation)

    def optimize_strategy(self, symbol: str, shifts, percentage: float) -> dict:
        if isinstance(shifts, (float, int)):
            shifts_iterable = [shifts]
        else:
            shifts_iterable = shifts

        try:
            backtest_result = self.backtester.run_backtest(symbol, shifts_iterable)
        except KeyError:
            backtest_result = {}
            
        try:
            simulation_result = self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            simulation_result = {}
            
        return {
            'backtest': backtest_result,
            'simulation': simulation_result
        }

    def evaluate_resilience(self, symbol: str, shifts) -> dict:
        if isinstance(shifts, (float, int)):
            shifts_iterable = [shifts]
        else:
            shifts_iterable = shifts

        try:
            stress_data = self.simulator.run_stress_test(symbol, shifts_iterable)
        except KeyError:
            stress_data = {}

        try:
            drawdown_checked = self.backtester.calculate_maximum_drawdown(symbol)
            if isinstance(drawdown_checked, str):
                drawdown_checked = float(drawdown_checked)
        except Exception:
            drawdown_checked = 0.0

        return {
            'stress_data': stress_data,
            'drawdown_checked': drawdown_checked
        }

    def load_strategy_stream(self, filepath: str):
        with open(filepath, 'rb') as f:
            return f.read()

    def optimize_and_evaluate(self, symbol: str, allocation: float, shifts) -> dict:
        validated_allocation = self._validate_allocation(allocation)

        if isinstance(shifts, (float, int)):
            shifts_iterable = [shifts]
        else:
            shifts_iterable = shifts

        try:
            backtest_res = self.backtester.run_backtest(symbol, shifts_iterable)
        except KeyError:
            backtest_res = {}

        try:
            stress_res = self.simulator.run_stress_test(symbol, shifts_iterable)
        except KeyError:
            stress_res = {}
        
        try:
            drawdown = self.backtester.calculate_maximum_drawdown(symbol)
            if isinstance(drawdown, str):
                drawdown = float(drawdown)
            resilience_score = 1.0 - abs(drawdown) if drawdown is not None else 0.5
        except Exception:
            drawdown = 0.0
            resilience_score = 0.5

        optimized_weights = {symbol: validated_allocation}
        
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
                "storage": getattr(self, 'storage_file', None)
            }
        }


MarketPortfolioStrategyOptimizer = PortfolioStrategyOptimizer
market_portfolio_strategy_optimizer = PortfolioStrategyOptimizer