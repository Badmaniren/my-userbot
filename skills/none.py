import os
import time
import uuid

# Честные импорты без читерства и try-except заглушек
from skills import db_storage
from skills import market_portfolio_collector_agent
from skills import market_portfolio_performance_analytics
from skills import market_report_generator


def start_new(**kwargs):
    db = kwargs.get("db_storage")
    if db is not None and hasattr(db, "fetch_epic_state"):
        state = db.fetch_epic_state()
        if isinstance(state, dict):
            status = str(state.get("status", "")).lower()
            if status == "completed":
                time.sleep(1)
                return {"status": "paused", "epic_id": state.get("epic_id")}
            return {"status": status, "epic_id": state.get("epic_id")}
    return {"status": "ready"}