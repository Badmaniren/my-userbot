from datetime import datetime
import json
import requests

from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine as default_mc_engine_import,
)
from skills.market_portfolio_stress_scenario_pipeline import (
    market_portfolio_stress_scenario_pipeline as default_scenario_pipeline_import,
)
from skills.market_portfolio_stress_auto_rebalance_trigger import (
    market_portfolio_stress_auto_rebalance_trigger as default_rebal_trigger_import,
)
from skills.db_storage import db_storage as default_db_storage_import

db_storage = default_db_storage_import


class MarketPortfolioStressPredictiveHedgeEngine:

    def __init__(
        self,
        db_storage=None,
        market_portfolio_stress_scenario_pipeline=None,
        market_portfolio_stress_monte_carlo_engine=None,
        market_portfolio_stress_auto_rebalance_trigger=None,
    ):
        self.db_storage = db_storage or default_db_storage_import

        scenario_pip = market_portfolio_stress_scenario_pipeline or default_scenario_pipeline_import
        self.scenario_pipeline = scenario_pip() if isinstance(scenario_pip, type) else scenario_pip

        mc_engine = market_portfolio_stress_monte_carlo_engine or default_mc_engine_import
        self.monte_carlo_engine = mc_engine() if isinstance(mc_engine, type) else mc_engine

        rebal_trigger = market_portfolio_stress_auto_rebalance_trigger or default_rebal_trigger_import
        self.auto_rebalance_trigger = rebal_trigger() if isinstance(rebal_trigger, type) else rebal_trigger

    def predict_and_rebalance(self, portfolio_id):
        try:
            scenario_result = self.scenario_pipeline.evaluate_scenario(portfolio_id)
            stress_level = scenario_result.get("stress_level")

            mc_result = self.monte_carlo_engine.simulate_stress(portfolio_id, scenario_result)
            predicted_drawdown = mc_result.get("predicted_drawdown", 0.0)
            recommended_hedges = mc_result.get("recommended_hedges", [])
            suggested_weights = mc_result.get("suggested_weights", [])

            if stress_level == "LOW" or predicted_drawdown < 0.05:
                return {
                    "status": "NO_ACTION_REQUIRED",
                    "portfolio_id": portfolio_id,
                }

            rebalance_res = self.auto_rebalance_trigger.execute_rebalance(
                portfolio_id, recommended_hedges, suggested_weights
            )

            timestamp = datetime.now().isoformat()
            event_record = {
                "portfolio_id": portfolio_id,
                "timestamp": timestamp,
                "hedges": recommended_hedges,
                "rebalance_status": rebalance_res.get("status"),
            }
            self.db_storage.save_hedge_event(event_record)

            return {
                "status": "SUCCESS",
                "portfolio_id": portfolio_id,
                "hedges": recommended_hedges,
                "rebalance": rebalance_res,
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "portfolio_id": portfolio_id,
                "error": str(e),
            }

    def evaluate_hedge_effectiveness_stream(self, url):
        response = requests.get(url, stream=True)
        content = response.raw.read()
        score = float(len(content) % 100) / 10.0
        return score


def market_portfolio_stress_predictive_hedge_engine(
    portfolio_id, rebalance_plan, output_path
):
    hedge_assets = rebalance_plan.get("recommended_hedges", ["GOLD", "USD"])

    result = {
        "target_portfolio": portfolio_id,
        "hedge_assets": hedge_assets,
        "status": "PREDICTED",
    }

    with open(output_path, "w") as f:
        json.dump(result, f)

    db_storage(
        query="INSERT INTO hedges (portfolio_id, assets) VALUES (?, ?)",
        params=(portfolio_id, str(hedge_assets)),
    )

    return result