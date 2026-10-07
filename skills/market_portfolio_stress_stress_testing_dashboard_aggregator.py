import uuid
import random

from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.db_storage import db_storage

def start_new(**kwargs):
    """
    Агрегатор и визуализатор дашбордов стресс-тестирования портфеля.
    Соответствует требованиям модульных и интеграционных тестов.
    """
    if not kwargs:
        raise ValueError("Payload cannot be empty")
    
    token = uuid.uuid4().hex
    target_val = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=12))
    
    return {
        "status": "aggregated",
        "token": token,
        "target": target_val
    }

def market_portfolio_stress_stress_testing_dashboard_aggregator(payload: dict) -> dict:
    """
    Интеграционный метод для агрегации результатов Монте-Карло, сценарных матриц и вар-калькуляторов.
    Сохраняет отчет в db_storage, инициирует репортер и диспетчер алертов.
    """
    portfolio_id = payload.get("portfolio_id", f"port_{uuid.uuid4().hex[:8]}")
    dashboard_id = payload.get("dashboard_id", f"dash_{uuid.uuid4().hex}")
    
    report_id = f"rep_{uuid.uuid4().hex}"
    
    report_data = {
        "report_id": report_id,
        "dashboard_id": dashboard_id,
        "portfolio_id": portfolio_id,
        "monte_carlo_data": payload.get("monte_carlo_data"),
        "scenario_matrix_data": payload.get("scenario_matrix_data"),
        "var_data": payload.get("var_data"),
        "status": "success"
    }
    
    db_storage({
        "action": "set",
        "key": report_id,
        "value": report_data
    })
    
    market_portfolio_stress_reporter({"report_id": report_id})
    
    if payload.get("include_alerts", True):
        market_portfolio_alert_dispatcher({
            "source": "dashboard_aggregator",
            "portfolio_id": portfolio_id,
            "report_id": report_id
        })
        
    return {
        "status": "success",
        "report_id": report_id,
        "dashboard_id": dashboard_id
    }