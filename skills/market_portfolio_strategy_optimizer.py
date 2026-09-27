from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class PortfolioStrategyOptimizer:
    def __init__(self, storage_file: str = "portfolio_optimizer.db"):
        self.storage_file = storage_file
        self.backtester = MarketPortfolioBacktester(storage_file)
        self.simulator = PortfolioScenarioSimulator(storage_file)

    def optimize_strategy(self, symbol_or_payload, shifts=None, percentage: float = 10.0) -> dict:
        if isinstance(symbol_or_payload, dict):
            portfolio_data = symbol_or_payload
            portfolio_id = portfolio_data.get("portfolio_id", "DEFAULT_PORTFOLIO")
            optimized_assets = {}
            total_tax_saving = 0.0

            for asset in portfolio_data.get("assets", []):
                ticker = asset.get("ticker", "UNKNOWN")
                shares = asset.get("shares", 0)
                cp = asset.get("current_price", 0.0)
                pp = asset.get("purchase_price", 0.0)

                gain = (cp - pp) * shares
                holding_days = asset.get("holding_period_days", 0)
                strategy = "HOLD_LONG_TERM" if holding_days >= 365 else "TAX_LOSS_HARVEST" if gain < 0 else "REBALANCE"

                optimized_assets[ticker] = {
                    "shares": shares,
                    "target_weight": round(1.0 / max(1, len(portfolio_data.get("assets", []))), 4),
                    "unrealized_gain": round(gain, 2),
                    "recommended_action": strategy
                }
                if strategy == "TAX_LOSS_HARVEST":
                    total_tax_saving += abs(gain) * 0.15

            return {
                "portfolio_id": portfolio_id,
                "status": "optimized",
                "estimated_tax_savings": round(total_tax_saving, 2),
                "optimized_assets": optimized_assets
            }

        symbol = symbol_or_payload
        if shifts is None:
            shifts = [1, 5]

        try:
            backtest_result = self.backtester.run_backtest(symbol, shifts)
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
        try:
            stress_data = self.simulator.run_stress_test(symbol, shifts)
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

        optimized_weights = {symbol: allocation}
        
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


MarketPortfolioStrategyOptimizer = PortfolioStrategyOptimizer


def market_portfolio_strategy_optimizer(storage_file: str = "portfolio_optimizer.db") -> PortfolioStrategyOptimizer:
    return PortfolioStrategyOptimizer(storage_file)