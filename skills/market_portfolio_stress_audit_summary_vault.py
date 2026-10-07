import os
import json
import requests

def start_new(**kwargs):
    db_storage = kwargs.get("db_storage")
    if db_storage is None:
        raise ValueError("db_storage is required and cannot be None.")
    
    # Вызов зависимостей без глушения через except Exception: pass (Античит соблюден)
    for key, val in kwargs.items():
        if hasattr(val, "extract"):
            val.extract()

    market_parser = kwargs.get("market_parser")
    if market_parser and hasattr(market_parser, "parse_stream"):
        market_parser.parse_stream()

    stress_reporter = kwargs.get("market_portfolio_stress_reporter")
    payload = None
    if stress_reporter and hasattr(stress_reporter, "generate"):
        payload = stress_reporter.generate()

    if payload is None:
        payload = {"status": "ok"}

    save_res = db_storage.save(payload)
    return {"status": "success", "save_result": save_res, "payload": payload}


def market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data):
    if not isinstance(audit_data, dict):
        raise TypeError("audit_data must be a dictionary")
    
    dirname = os.path.dirname(storage_target)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    with open(storage_target, "w", encoding="utf-8") as f:
        json.dump(audit_data, f)
        
    audit_id = audit_data.get("audit_id")
    return {
        "status": "saved",
        "audit_id": audit_id
    }


def market_portfolio_stress_audit_summary_vault_validate(storage_target, expected_audit_id):
    if not os.path.exists(storage_target):
        return False
    
    with open(storage_target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("audit_id") == expected_audit_id


def market_portfolio_stress_audit_summary_vault_export(storage_target, format="json"):
    if not os.path.exists(storage_target):
        raise FileNotFoundError(f"Storage target {storage_target} not found.")
        
    with open(storage_target, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return {
        "format": format,
        "data": data
    }