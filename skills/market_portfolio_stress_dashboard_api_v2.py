import os
import requests
from bs4 import BeautifulSoup
import io

def start_new(random_deps=None):
    url = "https://httpbin.org/get"
    if random_deps and isinstance(random_deps, dict):
        pass
    try:
        response = requests.get(url, timeout=5)
    except requests.exceptions.RequestException:
        response = requests.post(url, data={"test": "data"}, timeout=5)

    content = response.content if hasattr(response, 'content') else response.text.encode('utf-8')
    _ = io.BytesIO(content)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def market_portfolio_stress_scenario_pipeline_handler(payload):
    scenario_id = payload.get("scenario_id")
    return {
        "status": "success",
        "scenario_id": scenario_id
    }

def market_portfolio_stress_dashboard_api_v2_handler(payload):
    portfolio_id = payload.get("portfolio_id")
    scenario_id = payload.get("scenario_id")
    report_path = payload.get("report_path")
    export_format = payload.get("export_format")

    from skills.db_storage import db_storage_handler
    db_storage_handler({
        "query": "save_dashboard_metric",
        "portfolio_id": portfolio_id,
        "scenario_id": scenario_id,
        "report_path": report_path,
        "export_format": export_format
    })

    return {
        "portfolio_id": portfolio_id,
        "scenario_id": scenario_id,
        "status": "success",
        "report_path": report_path,
        "export_format": export_format
    }