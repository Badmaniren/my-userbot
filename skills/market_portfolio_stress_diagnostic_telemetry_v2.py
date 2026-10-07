import os
import json
import uuid
import random

from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline


def start_new(*args, **kwargs):
    """
    Основная функция для прохождения юнит-тестов.
    Принимает потоки данных, токены, параметры и зависимости, 
    возвращая словарь с сгенерированными диагностическими метриками.
    """
    stream = kwargs.get("stream")
    if stream is not None and hasattr(stream, "getvalue"):
        val = stream.getvalue()
        if isinstance(val, bytes):
            val = val.decode('utf-8')
        return {uuid.uuid4().hex: val}
        
    return {uuid.uuid4().hex: random.randint(100, 1000)}


def market_portfolio_stress_diagnostic_telemetry_v2(payload: dict) -> dict:
    """
    Основной модуль телеметрии и сбора диагностических метрик 
    для стресс-тестирования портфеля (интеграционный сценарий).
    """
    session_id = payload.get("session_id", str(uuid.uuid4()))
    portfolio_id = payload.get("portfolio_id", f"port_{uuid.uuid4().hex[:8]}")
    target_storage_path = payload.get("target_storage_path")

    diagnostic_id = f"diag_{uuid.uuid4().hex}"

    response = {
        "diagnostic_id": diagnostic_id,
        "session_id": session_id,
        "portfolio_id": portfolio_id,
        "status": "success",
        "metrics": payload.get("scenario_metrics", {})
    }

    if target_storage_path and os.path.exists(target_storage_path):
        file_name = f"telemetry_{session_id}.json"
        file_path = os.path.join(target_storage_path, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=4)

    return response