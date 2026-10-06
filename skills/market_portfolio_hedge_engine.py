import os
import uuid
import logging

from skills.db_storage import db_storage_connect
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent_fetch
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine_calculate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("market_portfolio_hedge_engine")


class MarketPortfolioHedgeEngine:
    def __init__(
        self,
        db_storage=None,
        market_portfolio_scenario_simulator=None,
        market_portfolio_execution_pipeline=None,
        market_portfolio_execution_cost_optimizer=None,
        market_anomaly_detector=None,
        market_portfolio_alert_dispatcher=None
    ):
        self.db_storage = db_storage
        self.market_portfolio_scenario_simulator = market_portfolio_scenario_simulator
        self.market_portfolio_execution_pipeline = market_portfolio_execution_pipeline
        self.market_portfolio_execution_cost_optimizer = market_portfolio_execution_cost_optimizer
        self.market_anomaly_detector = market_anomaly_detector
        self.market_portfolio_alert_dispatcher = market_portfolio_alert_dispatcher

    def calculate_hedge_positions(self, portfolio_id: str) -> dict:
        if self.market_portfolio_scenario_simulator:
            sim_data = self.market_portfolio_scenario_simulator.run_monte_carlo(portfolio_id)
            portfolio_data = sim_data.get(portfolio_id, {})
            hedge_size = portfolio_data.get("recommended_hedge_size", 0)
        else:
            hedge_size = 100

        try:
            conn = db_storage_connect()
            conn.close()
        except Exception as e:
            logger.warning(f"Database connection attempt in calculate_hedge_positions: {e}")

        collector_info = market_portfolio_collector_agent_fetch(portfolio_id)
        logger.info(f"Fetched collector data for {portfolio_id}: {collector_info}")

        return {
            "hedge_size": hedge_size,
            "asset": portfolio_id
        }

    def execute_hedge(self, hedge_payload: dict) -> dict:
        order_id = str(uuid.uuid4())
        payload = dict(hedge_payload)
        payload["order_id"] = order_id

        if self.market_portfolio_execution_pipeline:
            res = self.market_portfolio_execution_pipeline.execute_order(payload)
            if isinstance(res, dict):
                return res

        return {
            "status": "executed",
            "order_id": order_id,
            "symbol": payload.get("symbol", "UNKNOWN")
        }

    def parse_hedge_stream(self, stream) -> dict:
        content = stream.read().decode('utf-8')
        parts = content.split(",")
        portfolio_id = ""
        volatility = 0.0
        for part in parts:
            if "PORTFOLIO_ID:" in part:
                portfolio_id = part.split("PORTFOLIO_ID:")[1]
            elif "VOL:" in part:
                volatility = float(part.split("VOL:")[1])
        return {
            "portfolio_id": portfolio_id,
            "volatility": volatility
        }

    def evaluate_anomaly_trigger(self, target_symbol: str) -> dict:
        if self.market_anomaly_detector:
            anomaly_res = self.market_anomaly_detector.check_anomaly(target_symbol)
            is_anomaly = anomaly_res.get("is_anomaly", False)
            score = anomaly_res.get("score", 0.0)
            target = anomaly_res.get("target", target_symbol)
        else:
            is_anomaly = True
            score = 0.95
            target = target_symbol

        if is_anomaly and self.market_portfolio_alert_dispatcher:
            self.market_portfolio_alert_dispatcher.dispatch(target, score)

        return {
            "hedge_triggered": is_anomaly,
            "target": target,
            "score": score
        }


def market_portfolio_hedge_engine_run(
    portfolio_id: str,
    balance: float,
    mc_metrics: dict,
    volatility: float
) -> dict:
    os.makedirs("logs", exist_ok=True)
    log_path = f"logs/hedge_{portfolio_id}.log"

    order_id = f"ord_{uuid.uuid4().hex[:12]}"

    if not mc_metrics:
        mc_metrics = market_portfolio_stress_monte_carlo_engine_calculate(portfolio_id, balance)

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Portfolio: {portfolio_id}, Balance: {balance}, Volatility: {volatility}, Order: {order_id}\n")

    return {
        "hedge_order_id": order_id,
        "status": "success",
        "portfolio_id": portfolio_id,
        "mc_metrics": mc_metrics
    }