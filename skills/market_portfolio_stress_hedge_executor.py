import io
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline


class StressHedgeExecutorError(Exception):
    """Пользовательское исключение для ошибок выполнения хеджирования при стресс-тестировании."""
    pass


class MarketPortfolioStressHedgeExecutor:
    def __init__(self, storage_file: str = "stress_hedge_executor.db"):
        self.storage_file = storage_file
        self.stress_pipeline = PortfolioStressScenarioPipeline(storage_file=f"stress_{storage_file}")
        self.execution_pipeline = MarketPortfolioExecutionPipeline(storage_file=f"exec_{storage_file}")

    def calculate_and_execute_hedge(self, ticker: str, percentage: float, shifts: list, market_context: dict = None):
        if market_context is None:
            market_context = {}

        stress_result = self.stress_pipeline.execute(ticker, percentage, shifts)

        if not isinstance(stress_result, dict) or stress_result.get("status") == "failed":
            reason = stress_result.get("reason", "Unknown stress test failure") if isinstance(stress_result, dict) else "Invalid stress result"
            raise StressHedgeExecutorError(f"Stress test failed: {reason}")

        volume = stress_result.get("recommended_hedge_volume", 100)
        order_data = {"ticker": ticker, "volume": volume}

        try:
            execution_result = self.execution_pipeline.execute_order_simulation(
                order_data=order_data,
                market_context=market_context,
                percentage=percentage
            )
        except Exception as e:
            if isinstance(e, StressHedgeExecutorError):
                raise e
            raise StressHedgeExecutorError(f"Order execution simulation failed: {e}")

        return {
            "ticker": ticker,
            "stress_result": stress_result,
            "execution": execution_result
        }

    def run_batch_stress_hedges(self, tickers: list, percentage: float, shifts: list):
        results = []
        for ticker in tickers:
            res = self.calculate_and_execute_hedge(ticker, percentage, shifts)
            results.append(res)
        return results

    def simulate_hedge_stream(self, symbol: str, volume: int, stream_bytes: io.BytesIO):
        return self.execution_pipeline.simulate_execution(symbol, volume, stream_bytes)


def run_stress_hedge_execution_pipeline(
    scenario_pipeline_inst: PortfolioStressScenarioPipeline,
    execution_pipeline_inst: MarketPortfolioExecutionPipeline,
    ticker: str,
    percentage: float,
    shifts: list,
    volume: int
):
    stress_result = scenario_pipeline_inst.execute(
        symbol=ticker,
        percentage=percentage,
        shifts=shifts
    )

    if isinstance(stress_result, dict) and stress_result.get("status") == "failed":
        raise StressHedgeExecutorError("Stress test failed in integration pipeline")

    order_data = {"ticker": ticker, "volume": volume}
    market_context = {"pipeline": "integration"}

    try:
        execution_result = execution_pipeline_inst.execute_order_simulation(
            order_data=order_data,
            market_context=market_context,
            percentage=percentage
        )
    except Exception as e:
        if isinstance(e, StressHedgeExecutorError):
            raise e
        raise StressHedgeExecutorError(f"Order execution simulation failed: {e}")

    return {
        "ticker": ticker,
        "stress_result": stress_result,
        "execution": execution_result
    }