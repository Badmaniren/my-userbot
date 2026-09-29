from typing import Dict, Any, Optional
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator


class PortfolioStrategyOptimizer:
    def __init__(
        self,
        storage_file: Optional[str] = "default.db",
        target_portfolio: Optional[Dict[str, Any]] = None,
        initial_capital: float = 1000000.0,
        **kwargs
    ):
        if isinstance(storage_file, dict) and target_portfolio is None:
            self.target_portfolio = storage_file
            self.storage_file = kwargs.get("storage_path", "default.db")
        else:
            self.storage_file = storage_file or "default.db"
            self.target_portfolio = target_portfolio or {}

        self.initial_capital = initial_capital

        try:
            self.backtester = MarketPortfolioBacktester(self.storage_file)
        except Exception:
            self.backtester = None

        try:
            self.simulator = PortfolioScenarioSimulator(self.storage_file)
        except Exception:
            self.simulator = None

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
            shifts_iterable = list(shifts)

        backtest_result = {}
        if self.backtester and hasattr(self.backtester, "run_backtest"):
            try:
                backtest_result = self.backtester.run_backtest(symbol, shifts_iterable)
            except KeyError:
                backtest_result = {}

        simulation_result = {}
        if self.simulator and hasattr(self.simulator, "simulate_scenario"):
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
            shifts_iterable = list(shifts)

        stress_data = {}
        if self.simulator and hasattr(self.simulator, "run_stress_test"):
            try:
                stress_data = self.simulator.run_stress_test(symbol, shifts_iterable)
            except KeyError:
                stress_data = {}

        drawdown_checked = 0.0
        if self.backtester and hasattr(self.backtester, "calculate_maximum_drawdown"):
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
            shifts_iterable = list(shifts)

        backtest_res = {}
        if self.backtester and hasattr(self.backtester, "run_backtest"):
            try:
                backtest_res = self.backtester.run_backtest(symbol, shifts_iterable)
            except KeyError:
                backtest_res = {}

        stress_res = {}
        if self.simulator and hasattr(self.simulator, "run_stress_test"):
            try:
                stress_res = self.simulator.run_stress_test(symbol, shifts_iterable)
            except KeyError:
                stress_res = {}
        
        drawdown = 0.0
        resilience_score = 0.5
        if self.backtester and hasattr(self.backtester, "calculate_maximum_drawdown"):
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

    def optimize_hedge(self, risk_metrics: Optional[Dict[str, float]] = None, **kwargs) -> Dict[str, Any]:
        """Расчет параметров динамического хеджирования и защиты от хвостовых рисков."""
        metrics = risk_metrics or {}
        cvar = abs(metrics.get("cvar_95", metrics.get("cvar", 0.05)))
        var = abs(metrics.get("var_95", metrics.get("var", 0.03)))

        hedge_ratio = min(max(cvar * 5.0, 0.1), 1.0)
        hedge_notional = self.initial_capital * hedge_ratio
        protection_cost_pct = round(max(var * 0.5, 0.005), 4)

        return {
            "instrument": "PUT_OPTIONS",
            "hedge_notional": hedge_notional,
            "hedge_ratio": round(hedge_ratio, 2),
            "protection_cost_pct": protection_cost_pct,
            "status": "optimized"
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
