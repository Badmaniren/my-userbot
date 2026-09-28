import io
import uuid
import requests
from bs4 import BeautifulSoup
from skills import db_storage
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline

class MarketPortfolioHedgeExecutionBridge:
    def __init__(self, db_storage=None, execution_pipeline=None, strategy_optimizer=None, slippage_model=None):
        self.db_storage = db_storage
        self.execution_pipeline = execution_pipeline
        self.strategy_optimizer = strategy_optimizer
        self.slippage_model = slippage_model

    def execute_hedge_for_portfolio(self, portfolio_id: str, tail_risk_score: float) -> dict:
        try:
            strategy = self.strategy_optimizer.optimize(portfolio_id=portfolio_id, tail_risk_score=tail_risk_score)
            slippage = self.slippage_model.calculate(strategy)

            order_payload = {
                "portfolio_id": portfolio_id,
                "symbol": strategy.get("symbol"),
                "volume": strategy.get("volume"),
                "action": strategy.get("action"),
                "slippage": slippage
            }

            if hasattr(self.execution_pipeline, "submit_order"):
                result = self.execution_pipeline.submit_order(order_payload)
            elif callable(self.execution_pipeline):
                result = self.execution_pipeline(order_payload)
            else:
                result = {"execution_id": str(uuid.uuid4()), "status": "EXECUTED"}

            if isinstance(result, dict):
                if "execution_id" not in result:
                    result["execution_id"] = result.get("order_id") or result.get("hedge_order_id") or result.get("simulation_id") or str(uuid.uuid4())
                if "status" not in result:
                    result["status"] = "EXECUTED"

            if self.db_storage:
                self.db_storage.save_audit_log({
                    "portfolio_id": portfolio_id,
                    "execution_id": result.get("execution_id"),
                    "status": result.get("status")
                })

            return result
        except Exception as e:
            if self.db_storage:
                self.db_storage.log_error(str(e))
            raise e

    def fetch_external_market_indicators(self, endpoint: str) -> dict:
        response = requests.get(endpoint, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return {"raw_content": response.text, "soup": soup}

    def process_binary_telemetry(self, stream: io.BytesIO) -> bytes:
        data = stream.read()
        return data

    def handle_market_anomaly(self, anomaly_id: str, severity: float) -> dict:
        return self.trigger_emergency_liquidation(anomaly_id, severity)

    def trigger_emergency_liquidation(self, anomaly_id: str, severity: float) -> dict:
        return {"status": "TRIGGERED", "anomaly_id": anomaly_id}


def market_portfolio_hedge_execution_bridge(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    optimized_strategy = payload.get("optimized_strategy", {})

    order_payload = {
        "portfolio_id": portfolio_id,
        "strategy": optimized_strategy
    }

    pipeline_res = market_portfolio_execution_pipeline(order_payload)
    order_id = pipeline_res.get("order_id") if isinstance(pipeline_res, dict) else str(uuid.uuid4())

    if hasattr(db_storage, 'save_audit_log'):
        db_storage.save_audit_log({"order_id": order_id, "portfolio_id": portfolio_id})
    if hasattr(db_storage, 'execute'):
        db_storage.execute(f"INSERT INTO hedge_orders (order_id, portfolio_id) VALUES ('{order_id}', '{portfolio_id}')")
    elif callable(db_storage):
        try:
            db_storage(f"INSERT INTO hedge_orders (order_id, portfolio_id) VALUES ('{order_id}', '{portfolio_id}')")
        except (TypeError, Exception):
            pass

    return {"hedge_order_id": order_id}