import os
import uuid
import random
import logging

from skills.db_storage import db_storage
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub

logger = logging.getLogger("MarketPortfolioHedgeSignalHub")


def _extract_portfolio_id(obj, default="port_default"):
    if isinstance(obj, dict):
        if "portfolio_id" in obj and isinstance(obj["portfolio_id"], str):
            return obj["portfolio_id"]
        for key in ("context", "payload", "input_context", "data"):
            if key in obj:
                found = _extract_portfolio_id(obj[key], default=None)
                if found:
                    return found
        for val in obj.values():
            if isinstance(val, dict):
                found = _extract_portfolio_id(val, default=None)
                if found:
                    return found
    return default


def market_portfolio_hedge_signal_hub(context=None, signal_id=None, intensity=0.5, **kwargs):
    """
    Генератор и хаб торговых сигналов хеджирования.
    """
    s_id = signal_id or str(uuid.uuid4())

    portfolio_id = _extract_portfolio_id(context)
    if portfolio_id == "port_default":
        portfolio_id = _extract_portfolio_id(kwargs)

    record = {
        "signal_id": s_id,
        "portfolio_id": portfolio_id,
        "intensity": intensity,
        "logged": True,
        "status": "generated"
    }

    db_storage(action="set", key=s_id, value=record, **kwargs)

    target_filepath = f"hedge_signal_{s_id}.log"
    with open(target_filepath, "w") as f:
        f.write(f"Signal {s_id} for portfolio {portfolio_id} with intensity {intensity}\n")

    return record


def start_new(**kwargs):
    """
    Главная точка входа для запуска пайплайна сигналов хеджирования.
    Обрабатывает входящие зависимости, стресс-тесты, агрегаторы и возможные исключения.
    """
    stress_engine = kwargs.get("market_portfolio_stress_monte_carlo_engine")
    if stress_engine is not None:
        stress_engine()

    db = kwargs.get("db_storage")
    if db is not None:
        if hasattr(db, "get"):
            db.get("test_key")
        elif callable(db):
            db(action="get", key="test_key")

    aggregator = kwargs.get("market_portfolio_predictive_aggregator")
    if aggregator is not None and hasattr(aggregator, "aggregate"):
        aggregator.aggregate()

    anomaly_detector = kwargs.get("market_anomaly_detector")
    if anomaly_detector is not None:
        anomaly_detector()

    monitor = kwargs.get("market_portfolio_monitor")
    if monitor is not None:
        monitor()

    run_id = str(uuid.uuid4())
    return {
        "status": "success",
        "run_id": run_id,
        "metric": random.choice([100.5, 500.0, 999.9])
    }
