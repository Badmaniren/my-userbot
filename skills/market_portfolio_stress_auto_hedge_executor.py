from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline


class AutoHedgeExecutorError(Exception):
    """Исключение для ошибок автоматического хеджирования портфеля."""
    pass


class MarketPortfolioStressAutoHedgeExecutor:
    """
    Комбинирует советника по хеджированию и движок исполнения ордеров
    для автоматического применения защитных мер при стресс-сценариях портфеля.
    """

    def __init__(self, db_storage=None, hedge_advisor=None, execution_pipeline=None):
        self.db_storage = db_storage

        if hedge_advisor is not None:
            self.advisor = hedge_advisor
        else:
            try:
                self.advisor = MarketPortfolioStressHedgeAdvisor(db_storage=db_storage)
            except TypeError:
                self.advisor = MarketPortfolioStressHedgeAdvisor(
                    db_storage=db_storage,
                    monitor=None,
                    evaluator=None,
                    rebalancer=None
                )

        if execution_pipeline is not None:
            self.pipeline = execution_pipeline
        else:
            self.pipeline = MarketPortfolioExecutionPipeline(storage_file=db_storage)

    def execute_auto_hedge(self, portfolio_id: str, request_id: str) -> dict:
        try:
            advice = self.advisor.analyze_and_recommend(portfolio_id, request_id)
        except Exception as e:
            raise AutoHedgeExecutorError(str(e))

        recommendations = advice.get("recommendations", [])
        execution_results = []

        for rec in recommendations:
            order_data = dict(rec)
            if "ticker" not in order_data and "symbol" in order_data:
                order_data["ticker"] = order_data["symbol"]
            if "symbol" not in order_data and "ticker" in order_data:
                order_data["symbol"] = order_data["ticker"]

            try:
                res = self.pipeline.execute_order_simulation(
                    order_data,
                    market_context={"volatility": 0.2, "trend": "neutral", "liquidity_index": 1.0},
                    percentage=order_data.get("percentage_shift", -0.05)
                )
            except TypeError:
                res = self.pipeline.execute_order_simulation(order_data)
            execution_results.append(res)

        return {
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "execution_results": execution_results
        }

    def run_stress_hedge_scenario(self, ticker: str, volume: float, shifts: list, scenario_name: str) -> dict:
        return self.pipeline.run_stress_pipeline(ticker, shifts, volume, scenario_name)

    def stream_historical_audit_logs(self, simulation_id: str) -> list:
        return self.pipeline.get_historical_pipeline_logs(simulation_id)

    def execute_stress_hedge(self, portfolio_id: str, request_id: str, ticker: str, volume: float, shifts: list, market_context: dict) -> dict:
        stress_res = self.pipeline.run_stress_pipeline(ticker, shifts, volume, "integration_stress_scenario")

        try:
            advice = self.advisor.analyze_and_recommend(portfolio_id, request_id)
            recommendations = advice.get("recommendations", [])
        except Exception:
            recommendations = [
                {
                    "ticker": ticker,
                    "symbol": ticker,
                    "volume": volume,
                    "order_type": "SELL",
                    "price": 100.0,
                    "percentage_shift": shifts[0] if shifts else -0.05
                }
            ]

        if not recommendations:
            recommendations = [
                {
                    "ticker": ticker,
                    "symbol": ticker,
                    "volume": volume,
                    "order_type": "SELL",
                    "price": 100.0,
                    "percentage_shift": shifts[0] if shifts else -0.05
                }
            ]

        execution_results = []
        for rec in recommendations:
            order_data = dict(rec)
            if "ticker" not in order_data and "symbol" in order_data:
                order_data["ticker"] = order_data["symbol"]
            if "symbol" not in order_data and "ticker" in order_data:
                order_data["symbol"] = order_data["ticker"]

            percentage = order_data.get("percentage_shift")
            if percentage is None:
                percentage = shifts[0] if shifts else -0.05

            try:
                res = self.pipeline.execute_order_simulation(
                    order_data,
                    market_context=market_context,
                    percentage=percentage
                )
            except TypeError:
                res = self.pipeline.execute_order_simulation(order_data)
            execution_results.append(res)

        return {
            "execution_status": "COMPLETED",
            "recommendation_id": request_id,
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "stress_result": stress_res,
            "execution_results": execution_results
        }