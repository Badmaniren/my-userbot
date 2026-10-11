import uuid
import requests

from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics


def market_portfolio_transaction_cost_analyzer(
    portfolio_id,
    ticker,
    volume,
    exchange_fee_rate,
    slippage_metrics,
    liquidity_data
):
    estimated_slippage = 0.0
    total_cost = volume * exchange_fee_rate

    if isinstance(slippage_metrics, dict):
        estimated_slippage = slippage_metrics.get("estimated_slippage", 0.0)
        total_cost = slippage_metrics.get("total_cost", total_cost)

    total_transaction_cost = total_cost + (volume * estimated_slippage)
    impact_on_portfolio_return = - (total_transaction_cost / max(volume, 1.0))

    return {
        "status": "success",
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "volume": volume,
        "exchange_fee_rate": exchange_fee_rate,
        "total_transaction_cost": total_transaction_cost,
        "impact_on_portfolio_return": impact_on_portfolio_return,
        "liquidity_info": str(liquidity_data)
    }


def start_new(deps):
    if not isinstance(deps, dict):
        raise TypeError("Dependencies must be a dictionary")

    db = deps.get("db_storage")
    optimizer = deps.get("market_portfolio_execution_cost_optimizer")
    parser = deps.get("market_parser")
    anomaly_detector = deps.get("market_anomaly_detector")
    slippage_model = deps.get("market_portfolio_slippage_model")

    portfolio_id = uuid.uuid4().hex

    if db and hasattr(db, "fetch_portfolio"):
        portfolio_data = db.fetch_portfolio(portfolio_id)
        if isinstance(portfolio_data, dict):
            portfolio_id = portfolio_data.get("id", portfolio_id)

    if anomaly_detector and hasattr(anomaly_detector, "scan"):
        anomaly_detector.scan()

    if parser and hasattr(parser, "parse_stream"):
        parser.parse_stream()

    if slippage_model and hasattr(slippage_model, "estimate"):
        slippage_res = slippage_model.estimate()
        if isinstance(slippage_res, dict):
            return slippage_res

    if optimizer and hasattr(optimizer, "analyze"):
        return optimizer.analyze({
            "portfolio_id": portfolio_id,
            "assets": []
        })

    return {
        "status": "success",
        "portfolio_id": portfolio_id,
        "calculated_fee": 0.001,
        "spread": 0.05
    }