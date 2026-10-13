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


class StorageUnreachableError(Exception):
    """Исключение, выбрасываемое при недоступности хранилища."""
    pass


class MarketPortfolioStressAuditSummaryVault:
    """
    Класс для управления сводными данными аудита стресс-тестов портфеля.
    Хранит данные в общей памяти класса для корректного взаимодействия между компонентами.
    """
    _storage = {}

    def __init__(self, **kwargs):
        pass

    def save_summary(self, key, data):
        if not isinstance(key, str):
            key = str(key)
        MarketPortfolioStressAuditSummaryVault._storage[key] = data
        return {"status": "saved", "key": key}

    def get_summary(self, key):
        if not isinstance(key, str):
            key = str(key)
        return MarketPortfolioStressAuditSummaryVault._storage.get(key)

    def fetch_summary(self, key):
        return self.get_summary(key)

    def load_summary(self, key):
        return self.get_summary(key)

    def save_audit_summary(self, audit_id, summary_data):
        return self.save_summary(audit_id, summary_data)

    def get_audit_summary(self, audit_id):
        return self.get_summary(audit_id)

    def store_audit_data(self, audit_id, data):
        return self.save_summary(audit_id, data)

    def get_audit_data(self, audit_id):
        return self.get_summary(audit_id)

    def get_all_statuses(self):
        statuses = {}
        for k, v in MarketPortfolioStressAuditSummaryVault._storage.items():
            if isinstance(v, dict):
                statuses[k] = v.get("status")
            else:
                statuses[k] = str(v)
        return statuses


SummaryVault = MarketPortfolioStressAuditSummaryVault


def save_summary(key, summary_data):
    return MarketPortfolioStressAuditSummaryVault().save_summary(key, summary_data)


def get_summary(key):
    return MarketPortfolioStressAuditSummaryVault().get_summary(key)


def fetch_summary(key):
    return MarketPortfolioStressAuditSummaryVault().fetch_summary(key)


def store_audit_summary(summary_data):
    audit_id = None
    if isinstance(summary_data, dict):
        audit_id = summary_data.get("audit_id") or summary_data.get("subsystem")
    if not audit_id:
        import uuid
        audit_id = str(uuid.uuid4())
    MarketPortfolioStressAuditSummaryVault().save_summary(audit_id, summary_data)
    return audit_id


def get_audit_summary(audit_id):
    return MarketPortfolioStressAuditSummaryVault().get_audit_summary(audit_id)


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
    subsystem = audit_data.get("subsystem")
    vault = MarketPortfolioStressAuditSummaryVault()
    if audit_id:
        vault.save_summary(audit_id, audit_data)
    if subsystem:
        vault.save_summary(subsystem, audit_data)

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
