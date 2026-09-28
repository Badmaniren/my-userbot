import uuid
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline, ExecutionPipelineError

class MarketPortfolioRebalancePlanner:
    """
    Модуль автоматического планирования и исполнения ребалансировки портфеля.
    Координирует работу оптимизатора стратегий и пайплайна исполнения.
    """

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.optimizer = PortfolioStrategyOptimizer(storage_file=storage_path)
        self.execution_pipeline = MarketPortfolioExecutionPipeline(storage_file=storage_path)

    def plan_and_execute(self, symbol: str, shifts: int, percentage: float):
        """
        Рассчитывает целевую аллокацию и передает заявку в пайплайн исполнения.
        """
        optimization_result = self.optimizer.optimize_strategy(symbol, shifts, percentage)

        generated_order_id = uuid.uuid4().hex
        order_data = {
            "order_id": generated_order_id,
            "ticker": symbol,
            "symbol": symbol,
            "shifts": shifts,
            "optimization": optimization_result
        }
        market_context = {"symbol": symbol, "shifts": shifts, "adv": 100000, "volatility": 0.2, "spread_bps": 5.0}

        execution_result = self.execution_pipeline.execute_order_simulation(
            order_data,
            market_context,
            percentage
        )

        execution_id = None
        status = None
        if isinstance(execution_result, dict):
            if "execution_result" in execution_result and isinstance(execution_result["execution_result"], dict):
                exec_inner = execution_result["execution_result"]
            else:
                exec_inner = execution_result

            execution_id = exec_inner.get("order_id") or exec_inner.get("execution_id") or generated_order_id
            status = exec_inner.get("status") or ("executed" if execution_id else None)

        return {
            "execution_id": execution_id,
            "status": status
        }

    def run_batch_rebalance(self, symbols: list, percentage: float):
        """
        Выполняет пакетную ребалансировку для списка активов.
        """
        orders = []
        contexts = {}
        sym_list = symbols if isinstance(symbols, list) else [symbols]
        for sym in sym_list:
            try:
                opt_data = self.optimizer.optimize_and_evaluate(sym, percentage, 0)
            except Exception:
                opt_data = {}
            orders.append({
                "order_id": uuid.uuid4().hex,
                "ticker": sym,
                "symbol": sym,
                "percentage": percentage,
                "optimization": opt_data
            })
            contexts[sym] = {"symbol": sym, "adv": 100000, "volatility": 0.2, "spread_bps": 5.0}

        return self.execution_pipeline.run_batch_pipeline_execution(orders, contexts, percentage)

    def get_rebalance_readiness(self, symbol: str):
        """
        Получает сводку стратегии для оценки готовности к ребалансировке.
        """
        return self.optimizer.get_strategy_summary(symbol)

    def verify_stress_resilience(self, ticker: str, shifts: list, volume: int, scenario: str):
        """
        Проверяет устойчивость стратегии через стресс-тестирование пайплайна.
        """
        return self.execution_pipeline.run_stress_pipeline(ticker, shifts, volume, scenario)
