from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_execution_pipeline import (
    MarketPortfolioExecutionPipeline,
    ExecutionPipelineError
)

class HedgeOrderRouterError(Exception):
    """Кастомное исключение для ошибок маршрутизатора ордеров хеджирования."""
    pass

class MarketPortfolioHedgeOrderRouter:
    def __init__(self, storage_file=None, stress_sync_module=None, execution_pipeline=None):
        self.storage_file = storage_file
        self.stress_sync = stress_sync_module or MarketPortfolioStressAutoHedgeSync(storage_file=storage_file)
        self.pipeline = execution_pipeline or MarketPortfolioExecutionPipeline(storage_file=storage_file)

    def _validate(self, portfolio_id, symbol, percentage, shifts):
        if not portfolio_id or not isinstance(portfolio_id, str):
            raise HedgeOrderRouterError("Invalid portfolio_id")
        if not symbol or not isinstance(symbol, str):
            raise HedgeOrderRouterError("Invalid symbol")
        if percentage is None or percentage < 0:
            raise HedgeOrderRouterError("Invalid percentage")
        if not shifts or not isinstance(shifts, list):
            raise HedgeOrderRouterError("Invalid shifts")

    def _execute_pipeline(self, symbol, recommended_volume, percentage, request_id=None):
        market_context = {"adv": 100000, "volatility": 0.2, "spread_bps": 5.0}
        order_data = {
            "symbol": symbol,
            "ticker": symbol,
            "volume": recommended_volume,
            "quantity": recommended_volume,
            "order_id": request_id
        }

        try:
            return self.pipeline.execute_order_simulation(
                order_data=order_data,
                market_context=market_context,
                percentage=percentage
            )
        except TypeError:
            return self.pipeline.execute_order_simulation(
                order_data,
                market_context,
                percentage
            )

    def route_and_execute_hedge(self, portfolio_id, request_id, symbol, percentage, shifts):
        self._validate(portfolio_id, symbol, percentage, shifts)

        sync_result = self.stress_sync.synchronize(portfolio_id, request_id, symbol, percentage, shifts)

        hedge_signal = sync_result.get("hedge_signal", {})
        recommended_volume = hedge_signal.get("recommended_volume", 100)

        try:
            execution_result = self._execute_pipeline(symbol, recommended_volume, percentage, request_id=request_id)
        except ExecutionPipelineError as e:
            raise HedgeOrderRouterError(f"Execution pipeline failed: {e}")
        except Exception as e:
            raise HedgeOrderRouterError(f"Unexpected execution error: {e}")

        return {
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "sync_result": sync_result,
            "execution_result": execution_result
        }

    def route_hedge_signal(self, portfolio_id, request_id, symbol, percentage, shifts):
        self._validate(portfolio_id, symbol, percentage, shifts)

        sync_result = self.stress_sync.synchronize(portfolio_id, request_id, symbol, percentage, shifts)

        hedge_signal = sync_result.get("hedge_signal", {})
        recommended_volume = hedge_signal.get("recommended_volume", 100)

        try:
            execution_result = self._execute_pipeline(symbol, recommended_volume, percentage, request_id=request_id)
        except ExecutionPipelineError as e:
            raise HedgeOrderRouterError(f"Execution pipeline failed: {e}")
        except Exception as e:
            raise HedgeOrderRouterError(f"Unexpected execution error: {e}")

        return {
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "sync_status": sync_result.get("status", "success"),
            "sync_result": sync_result,
            "execution_result": execution_result
        }

    def get_router_execution_logs(self, sim_id):
        return self.pipeline.get_historical_pipeline_logs(sim_id)

    def execute_batch_hedges(self, orders, contexts, percentage):
        try:
            return self.pipeline.run_batch_pipeline_execution(orders, contexts, percentage)
        except Exception as e:
            try:
                return self.pipeline.run_batch_pipeline_execution(orders, percentage=percentage)
            except Exception:
                raise ExecutionPipelineError(f"Error in run_batch_pipeline_execution: {e}")