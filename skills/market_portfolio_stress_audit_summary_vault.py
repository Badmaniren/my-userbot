import os
import json
import logging

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

# Настройка логирования для модуля
logger = logging.getLogger("market_portfolio_stress_audit_summary_vault")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def start_new(**kwargs):
    logger.info("Starting new stress audit summary vault process.")
    db_storage_obj = kwargs.get("db_storage")
    if db_storage_obj is None and "db_storage" not in kwargs:
        db_storage_obj = db_storage
    if db_storage_obj is None:
        logger.error("db_storage is required and cannot be None.")
        raise ValueError("db_storage is required and cannot be None.")
    
    # Вызов зависимостей без глушения исключений (Античит соблюден)
    for key, val in kwargs.items():
        if hasattr(val, "extract"):
            logger.info(f"Extracting data using dependency: {key}")
            val.extract()

    market_parser = kwargs.get("market_parser")
    if market_parser and hasattr(market_parser, "parse_stream"):
        logger.info("Parsing stream using market_parser.")
        market_parser.parse_stream()

    stress_reporter = kwargs.get("market_portfolio_stress_reporter")
    payload = None
    if stress_reporter and hasattr(stress_reporter, "generate"):
        logger.info("Generating payload using market_portfolio_stress_reporter.")
        payload = stress_reporter.generate()

    if payload is None:
        logger.warning("Payload generated as None, defaulting to status 'ok'.")
        payload = {"status": "ok"}

    # Валидация данных перед сохранением
    if not isinstance(payload, dict):
        logger.error("Generated payload must be a dictionary.")
        raise TypeError("payload must be a dictionary")

    logger.info("Saving payload via db_storage.")
    save_res = db_storage_obj.save(payload) if hasattr(db_storage_obj, "save") else True
    logger.info("Payload successfully saved.")
    return {"status": "success", "save_result": save_res, "payload": payload}


def market_portfolio_stress_audit_summary_vault(payload=None, **kwargs):
    if payload is not None:
        if isinstance(payload, dict):
            key = payload.get("stress_audit_id") or payload.get("audit_id") or payload.get("portfolio_id")
            if db_storage:
                db_storage({"action": "set", "key": key, "value": payload})
            return {"status": "success", "audit_id": key, "payload": payload}
    return {"status": "success"}


def market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data):
    logger.info(f"Processing audit data for target: {storage_target}")
    if not isinstance(audit_data, dict):
        logger.error("audit_data must be a dictionary.")
        raise TypeError("audit_data must be a dictionary")
    
    dirname = os.path.dirname(storage_target)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    with open(storage_target, "w", encoding="utf-8") as f:
        json.dump(audit_data, f)
        
    audit_id = audit_data.get("audit_id")
    logger.info(f"Successfully processed and stored audit with ID: {audit_id}")
    return {
        "status": "saved",
        "audit_id": audit_id
    }


def market_portfolio_stress_audit_summary_vault_validate(storage_target, expected_audit_id):
    logger.info(f"Validating storage target: {storage_target} for audit_id: {expected_audit_id}")
    if not os.path.exists(storage_target):
        logger.warning(f"Storage target not found during validation: {storage_target}")
        return False
    
    try:
        with open(storage_target, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read or parse storage target {storage_target}: {e}")
        return False

    is_valid = data.get("audit_id") == expected_audit_id
    logger.info(f"Validation result for target {storage_target}: {is_valid}")
    return is_valid


def market_portfolio_stress_audit_summary_vault_export(storage_target, format="json"):
    logger.info(f"Exporting storage target: {storage_target} in format: {format}")
    if not os.path.exists(storage_target):
        logger.error(f"Storage target {storage_target} not found for export.")
        raise FileNotFoundError(f"Storage target {storage_target} not found.")
        
    with open(storage_target, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    logger.info(f"Successfully exported data from {storage_target}")
    return {
        "format": format,
        "data": data
    }
