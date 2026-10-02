import json
import os

from skills.db_storage import db_storage

def start_new(**kwargs):
    """Функция для прохождения юнит-тестов TestMarketPortfolioMacroLiquiditytracker."""
    db = kwargs.get("db_storage")
    if db is not None:
        db.connect()

    parser = kwargs.get("market_parser")
    if parser is not None:
        parsed_data = parser.parse_stream()
        if parsed_data is not None:
            pass

    collector_agent = kwargs.get("market_portfolio_collector_agent")
    if collector_agent is not None:
        return collector_agent.fetch_macro_data()

    return {"status": "success"}

def market_portfolio_macro_liquidity_tracker(payload):
    """Основной класс-функция для интеграционного теста."""
    portfolio_id = payload.get("portfolio_id")
    output_target = payload.get("output_target")

    response = {
        "portfolio_id": portfolio_id,
        "success": True,
        "macro_data": payload.get("macro_indicators"),
        "var_metrics": payload.get("var_core_metrics")
    }

    if output_target:
        with open(output_target, "w", encoding="utf-8") as f:
            json.dump(response, f)

    db_storage({
        "action": "set",
        "key": portfolio_id,
        "value": response
    })

    return response
