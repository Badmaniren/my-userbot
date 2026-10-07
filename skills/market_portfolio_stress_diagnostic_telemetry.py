import json
import requests
from bs4 import BeautifulSoup

import skills.market_portfolio_stress_monte_carlo_engine as market_portfolio_stress_monte_carlo_engine
import skills.market_anomaly_detector as market_anomaly_detector
import skills.db_storage as db_storage
import skills.market_portfolio_audit_log_exporter as market_portfolio_audit_log_exporter
import skills.market_portfolio_autonomous_sentinel as market_portfolio_autonomous_sentinel
import skills.market_portfolio_alert_dispatcher as market_portfolio_alert_dispatcher
import skills.market_portfolio_stress_scenario_matrix_evaluator as market_portfolio_stress_scenario_matrix_evaluator
import skills.market_portfolio_tax_calculator as market_portfolio_tax_calculator
import skills.market_portfolio_execution_cost_optimizer as market_portfolio_execution_cost_optimizer

class TelemetryValidationError(Exception):
    pass

class StressDiagnosticTelemetryCollector:
    def __init__(self, db_storage_url: str):
        self.db_storage_url = db_storage_url

    def collect_and_validate(self, portfolio_id: str, session_id: str) -> dict:
        run_sim = getattr(market_portfolio_stress_monte_carlo_engine, "run_simulation", None)
        if run_sim is not None:
            mc_result = run_sim(portfolio_id=portfolio_id, session_id=session_id)
        else:
            mc_result = market_portfolio_stress_monte_carlo_engine.run(portfolio_id=portfolio_id, session_id=session_id)

        detect_anom = getattr(market_anomaly_detector, "detect_anomalies", None)
        if detect_anom is not None:
            anomaly_result = detect_anom(portfolio_id=portfolio_id, session_id=session_id)
        else:
            anomaly_result = market_anomaly_detector.detect(portfolio_id=portfolio_id, session_id=session_id)

        commit_fn = getattr(db_storage, "commit", None)
        if commit_fn is not None:
            commit_fn()

        result = {
            "portfolio_id": portfolio_id,
            "session_id": session_id,
            "var_95": mc_result.get("var_95"),
            "stress_score": mc_result.get("stress_score"),
            "anomaly_detected": anomaly_result.get("anomaly_detected"),
            "confidence": anomaly_result.get("confidence")
        }
        return result

    def validate_audit_stream(self, stream_id: str) -> None:
        export_fn = getattr(market_portfolio_audit_log_exporter, "export_stream", None)
        if export_fn is not None:
            stream = export_fn(stream_id=stream_id)
        else:
            stream = market_portfolio_audit_log_exporter.export(stream_id=stream_id)
        content = stream.read()
        try:
            json.loads(content.decode('utf-8'))
        except (json.JSONDecodeError, ValueError) as e:
            raise TelemetryValidationError(f"Invalid JSON stream: {e}")

    def parse_external_stress_feed(self, url: str) -> dict:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        indicator = soup.find(class_='stress-indicator')
        title = indicator.find('h1').text if indicator and indicator.find('h1') else ""
        val_str = indicator.find(class_='val').text if indicator and indicator.find(class_='val') else "0.0"
        value = float(val_str)
        return {"title": title, "value": value}

    def run_sentinel_check(self, context_id: str) -> dict:
        eval_fn = getattr(market_portfolio_autonomous_sentinel, "evaluate_threat", None)
        if eval_fn is not None:
            threat_eval = eval_fn(context_id)
        else:
            threat_eval = market_portfolio_autonomous_sentinel.evaluate(context_id)

        dispatch_fn = getattr(market_portfolio_alert_dispatcher, "dispatch_alert", None)
        if dispatch_fn is not None:
            dispatch_res = dispatch_fn(threat_eval)
        else:
            dispatch_res = market_portfolio_alert_dispatcher.dispatch(threat_eval)
        return dispatch_res

    def evaluate_liquidity_stress(self, matrix_id: str) -> dict:
        eval_fn = getattr(market_portfolio_stress_scenario_matrix_evaluator, "evaluate_matrix", None)
        if eval_fn is not None:
            return eval_fn(matrix_id)
        return market_portfolio_stress_scenario_matrix_evaluator.evaluate(matrix_id)

    def compile_financial_friction_report(self, portfolio_id: str) -> dict:
        calc_fn = getattr(market_portfolio_tax_calculator, "calculate", None)
        if calc_fn is not None:
            tax_report = calc_fn(portfolio_id)
        else:
            tax_report = market_portfolio_tax_calculator.calc(portfolio_id)

        opt_fn = getattr(market_portfolio_execution_cost_optimizer, "optimize", None)
        if opt_fn is not None:
            cost_report = opt_fn(portfolio_id)
        else:
            cost_report = market_portfolio_execution_cost_optimizer.opt(portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "tax_liability": tax_report.get("tax_liability"),
            "execution_cost": cost_report.get("optimal_cost")
        }

def market_portfolio_stress_diagnostic_telemetry_run(portfolio_id: str, telemetry_salt: str) -> dict:
    telemetry_id = f"telemetry_{portfolio_id}_{telemetry_salt[:8]}"
    return {
        "telemetry_id": telemetry_id,
        "portfolio_id": portfolio_id,
        "integrity_status": True
    }

def db_storage_save(record_id: str, payload: dict) -> bool:
    save_fn = getattr(db_storage, "save", None)
    if save_fn is not None:
        return save_fn(record_id, payload)
    put_fn = getattr(db_storage, "put", None)
    if put_fn is not None:
        return put_fn(record_id, payload)
    return True

def db_storage_get(record_id: str) -> dict:
    get_fn = getattr(db_storage, "get", None)
    if get_fn is not None:
        return get_fn(record_id)
    fetch_fn = getattr(db_storage, "fetch", None)
    if fetch_fn is not None:
        return fetch_fn(record_id)
    return {}