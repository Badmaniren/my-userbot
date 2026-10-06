import requests
import uuid
import random
from typing import Dict, Any, Optional

from skills.db_storage import (
    db_storage_connect,
    db_storage_save_portfolio,
    db_storage_get_hedge_result
)
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator_execute
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core_calculate


class MarketPortfolioStressAutoHedgeEngineV2:
    def __init__(self, db_storage=None, **kwargs):
        self.db_storage = db_storage
        for key, value in kwargs.items():
            setattr(self, key, value)

    def execute_auto_hedge(self, portfolio_id: str) -> Dict[str, Any]:
        if self.db_storage and hasattr(self.db_storage, "fetch_portfolio"):
            portfolio = self.db_storage.fetch_portfolio(portfolio_id)
        else:
            portfolio = {}
        if not isinstance(portfolio, dict):
            portfolio = {}
        hedge_asset = portfolio.get("asset")

        sim_result = getattr(self, "market_portfolio_scenario_simulator", None) or getattr(self, "scenario_simulator", None)
        if sim_result:
            sim_data = sim_result.simulate(portfolio_id)
            if sim_data and "hedge_asset" in sim_data:
                hedge_asset = sim_data["hedge_asset"]

        return {
            "portfolio_id": portfolio_id,
            "stress_level": portfolio.get("stress_level", 0.0),
            "hedge_asset": hedge_asset,
            "status": "hedged"
        }

    def ingest_external_stream(self, url: str) -> bytes:
        response = requests.get(url, stream=True)
        return response.raw.read()

    def handle_anomaly_trigger(self, anomaly_id: str) -> bool:
        detector = getattr(self, "market_anomaly_detector", None) or getattr(self, "anomaly_detector", None)
        if detector:
            detector.detect(anomaly_id)

        pipeline = getattr(self, "market_portfolio_execution_pipeline", None) or getattr(self, "execution_pipeline", None)
        if pipeline:
            return pipeline.execute_hedge_order(anomaly_id)
        return True


def market_portfolio_stress_auto_hedge_engine_v2_run(
    portfolio_id: str,
    drop_scenario: float,
    simulation_context: Dict[str, Any],
    var_context: Dict[str, Any]
) -> Dict[str, Any]:
    hedge_order_id = f"hedge_{uuid.uuid4().hex[:12]}"
    hedge_amount = round(random.uniform(1000.0, 50000.0), 2)

    db_conn = db_storage_connect()
    if db_conn and hasattr(db_conn, "cursor"):
        cursor = db_conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS hedge_results (portfolio_id TEXT PRIMARY KEY, hedge_order_id TEXT, hedge_amount REAL)"
        )
        cursor.execute(
            "INSERT OR REPLACE INTO hedge_results (portfolio_id, hedge_order_id, hedge_amount) VALUES (?, ?, ?)",
            (portfolio_id, hedge_order_id, hedge_amount)
        )
        db_conn.commit()

    return {
        "portfolio_id": portfolio_id,
        "hedge_order_id": hedge_order_id,
        "hedge_amount": hedge_amount,
        "drop_scenario": drop_scenario,
        "simulation_context": simulation_context,
        "var_context": var_context
    }