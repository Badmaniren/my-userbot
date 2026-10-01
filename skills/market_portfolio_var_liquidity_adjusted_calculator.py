import os
from skills.db_storage import db_storage

class MarketPortfolioVarLiquidityAdjustedCalculator:
    def __init__(self, db_storage=None, extractor_tool_1790087207=None, market_anomaly_detector=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool_1790087207
        self.market_anomaly_detector = market_anomaly_detector

    def _fetch_market_depth(self, portfolio_id: str) -> dict:
        if self.extractor_tool:
            return self.extractor_tool.fetch(portfolio_id)
        return {"depth": 100000, "volatility": 0.02, "spread": 0.001}

    def compute_lvar(self, portfolio_id: str, confidence_level: float = 0.95, time_horizon_days: int = 1) -> dict:
        if self.market_anomaly_detector:
            self.market_anomaly_detector.check_anomaly(portfolio_id)

        market_data = self._fetch_market_depth(portfolio_id)
        depth = market_data.get("depth", 100000)
        vol = market_data.get("volatility", 0.02)

        lvar_val = float(depth) * float(vol) * (time_horizon_days ** 0.5)

        return {
            "lvar": lvar_val,
            "portfolio_id": portfolio_id,
            "confidence_level": confidence_level,
            "time_horizon_days": time_horizon_days
        }

    def estimate_liquidity_cost(self, position_size: float, stream_path: str) -> float:
        with open(stream_path, "r", encoding="utf-8") as f:
            content = f.read()

        volume = 1000000.0
        spread = 0.01
        for part in content.split(","):
            if "volume" in part:
                try:
                    volume = float(part.split(":")[1])
                except (ValueError, IndexError):
                    raise
            elif "spread" in part:
                try:
                    spread = float(part.split(":")[1])
                except (ValueError, IndexError):
                    raise

        cost = (position_size / max(volume, 1.0)) * spread * 1000.0
        return float(max(cost, 0.0))

    def persist_lvar_result(self, portfolio_id: str, lvar_value: float):
        if self.db_storage:
            self.db_storage.save_metric(portfolio_id, lvar_value)


def market_portfolio_var_liquidity_adjusted_calculator(
    portfolio_id: str,
    valuation: dict,
    slippage: dict,
    confidence_level: float = 0.95,
    holding_period_days: int = 1
):
    val_amount = valuation.get("valuation", 1000.0) if isinstance(valuation, dict) else 1000.0
    slip_cost = slippage.get("slippage", 10.0) if isinstance(slippage, dict) else 10.0

    l_var_value = float(val_amount) * 0.05 * (holding_period_days ** 0.5) + float(slip_cost)

    result = {
        "l_var_value": l_var_value,
        "portfolio_id": portfolio_id,
        "confidence_level": confidence_level,
        "holding_period_days": holding_period_days,
        "persisted": True
    }

    output_filepath = f"report_{portfolio_id}.json"
    if not os.path.exists(output_filepath):
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(str(result))

    return result