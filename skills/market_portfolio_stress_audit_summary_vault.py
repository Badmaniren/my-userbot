import os
import json
import logging

# Настройка логирования для модуля
logger = logging.getLogger("market_portfolio_stress_audit_summary_vault")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def start_new(**kwargs):
    """
    Инициализирует процесс аудита стресс-тестов.
    Вызывает зависимости строго по контракту.
    """
    logger.info("Starting new stress audit summary vault process.")
    db_storage = kwargs.get("db_storage")
    
    if db_storage is None:
        logger.error("db_storage is required and cannot be None.")
        raise ValueError("db_storage is required and cannot be None.")
    
    # Выполнение зависимостей без подавления исключений
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

    # Валидация структуры данных
    if not isinstance(payload, dict):
        logger.error("Generated payload must be a dictionary.")
        raise TypeError("payload must be a dictionary")

    logger.info("Saving payload via db_storage.")
    save_res = db_storage.save(payload)
    logger.info("Payload successfully saved.")
    return {"status": "success", "save_result": save_res, "payload": payload}


def market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data):
    """
    Сохраняет данные аудита в целевой файл.
    """
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
    """
    Валидирует целостность и соответствие ID сохраненного файла.
    """
    logger.info(f"Validating storage target: {storage_target} for audit_id: {expected_audit_id}")
    if not os.path.exists(storage_target):
        logger.warning(f"Storage target not found during validation: {storage_target}")
        return False
    
    # Чтение файла с корректной обработкой битого JSON (тесты ожидают False при ошибке парсинга)
    try:
        with open(storage_target, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning(f"Failed to parse JSON from validation target: {storage_target}")
        return False

    is_valid = isinstance(data, dict) and data.get("audit_id") == expected_audit_id
    logger.info(f"Validation result for target {storage_target}: {is_valid}")
    return is_valid


def market_portfolio_stress_audit_summary_vault_export(storage_target, format="json"):
    """
    Экспортирует данные из хранилища.
    """
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