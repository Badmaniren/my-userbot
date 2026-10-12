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


class SummaryVault:
    def __init__(self, storage_path=None, **kwargs):
        self.storage_path = storage_path or kwargs.get("storage_target") or kwargs.get("file_path")

    def load_summary(self):
        if not self.storage_path or not os.path.exists(self.storage_path):
            raise FileNotFoundError(f"Storage path {self.storage_path} does not exist.")
        with open(self.storage_path, "r", encoding="utf-8") as f:
            return json.load(f)


def market_portfolio_stress_audit_summary_vault(*args, **kwargs):
    if args and isinstance(args[0], str):
        return SummaryVault(storage_path=args[0])
    if "storage_path" in kwargs or "storage_target" in kwargs or "file_path" in kwargs:
        return SummaryVault(**kwargs)
    return start_new(**kwargs)


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


# Алиасы для обратной совместимости
start_neos = start_new
market_portfolio_stress_audit_summary_vault_start = start_new


def market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data):
    """
    Сохраняет данные аудита в целевой файл с детерминированной сериализацией.
    """
    logger.info(f"Processing audit data for target: {storage_target}")
    if not isinstance(audit_data, dict):
        logger.error("audit_data must be a dictionary.")
        raise TypeError("audit_data must be a dictionary")

    dirname = os.path.dirname(storage_target)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(storage_target, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, sort_keys=True)

    audit_id = audit_data.get("audit_id")
    return {"status": "saved", "audit_id": audit_id}


def market_portfolio_stress_audit_summary_vault_validate(file_path, expected_audit_id):
    """
    Проверяет валидность JSON-файла и совпадение audit_id.
    """
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return False

    if not isinstance(data, dict):
        return False

    return data.get("audit_id") == expected_audit_id


def market_portfolio_stress_audit_summary_vault_export(file_path, format="json"):
    """
    Экспортирует данные стресс-аудита из файла.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "format": format,
        "data": data
    }
