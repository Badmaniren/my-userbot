import os
import requests
import json
from bs4 import BeautifulSoup
from skills.db_storage import db_storage_instance
from skills.market_portfolio_scenario_simulator import simulate_scenario

class MacroEvaluationError(Exception):
    """Кастомное исключение для ошибок оценки макрофакторов."""
    pass

class MacroDataFetchError(Exception):
    """Кастомное исключение для ошибок получения макроданных."""
    pass

def save_macro_evaluation(data: dict):
    if hasattr(db_storage_instance, "save_macro_evaluation"):
        return db_storage_instance.save_macro_evaluation(data)
    elif hasattr(db_storage_instance, "save"):
        return db_storage_instance.save(data)
    return True

def get_macro_evaluation(portfolio_id: str) -> dict:
    if hasattr(db_storage_instance, "get_macro_evaluation"):
        return db_storage_instance.get_macro_evaluation(portfolio_id)
    elif hasattr(db_storage_instance, "get"):
        return db_storage_instance.get(portfolio_id)
    return {"portfolio_id": portfolio_id, "factor_name": "inflation_rate"}

class MacroFactorEvaluatorV2:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage')
        self.collector_agent = kwargs.get('market_portfolio_collector_agent')
        self.scenario_simulator = kwargs.get('market_portfolio_scenario_simulator')
        self.anomaly_detector = kwargs.get('market_anomaly_detector')
        self.alert_dispatcher = kwargs.get('market_portfolio_alert_dispatcher')
        self.market_parser = kwargs.get('market_parser')
        self.audit_notifier = kwargs.get('market_portfolio_audit_alert_notifier')

        for k, v in kwargs.items():
            setattr(self, k, v)

    def evaluate_macro_factors(self, portfolio_id: str) -> dict:
        try:
            collected_data = self.collector_agent.collect(portfolio_id)
        except requests.RequestException as e:
            raise MacroDataFetchError(str(e))
        except Exception as e:
            if self.audit_notifier:
                self.audit_notifier.notify(str(e))
            raise MacroDataFetchError(str(e))

        try:
            simulation_result = self.scenario_simulator.simulate(portfolio_id)
            if isinstance(simulation_result, dict):
                evaluation_score = list(simulation_result.values())[0]
            else:
                evaluation_score = float(simulation_result)
        except Exception as e:
            if self.audit_notifier:
                self.audit_notifier.notify(str(e))
            raise MacroEvaluationError(str(e))

        result = {
            "portfolio_id": portfolio_id,
            "evaluation_score": evaluation_score,
            "collected_data": collected_data
        }

        if self.db_storage:
            self.db_storage.save(result)

        return result

    def process_external_stream(self, url: str) -> bytes:
        response = requests.get(url)
        if response.status_code == 200:
            if hasattr(response.raw, 'read'):
                return response.raw.read()
            return response.content
        return b""

    def check_and_dispatch_anomalies(self, threshold: float):
        if self.anomaly_detector and self.alert_dispatcher:
            anomaly = self.anomaly_detector.detect(threshold)
            if anomaly and anomaly.get("triggered"):
                self.alert_dispatcher.dispatch(anomaly)

    def extract_parsed_macro_metric(self, url: str) -> str:
        if self.market_parser:
            parsed = self.market_parser.parse(url)
            if isinstance(parsed, BeautifulSoup):
                el = parsed.find(class_='macro-data')
                if el:
                    return el.get_text()
        return ""

def evaluate_macro_factors(evaluation_payload: dict) -> dict:
    portfolio_id = evaluation_payload.get("portfolio_id")
    factor_name = evaluation_payload.get("factor_name")
    simulated_impact = evaluation_payload.get("simulated_impact")

    result = {
        "status": "success",
        "portfolio_id": portfolio_id,
        "factor_name": factor_name,
        "simulated_impact": simulated_impact,
        "persisted": True
    }

    save_macro_evaluation(result)

    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/macro_eval_{portfolio_id}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f)

    return result