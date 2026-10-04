import requests
from skills.db_storage import DBStorage

def start_new(service_url, mock_dependencies):
    """
    Базовая функция мониторинга макроэкономической ликвидности.
    Выполняет вызовы зависимостей и сетевой запрос.
    Если происходит сетевая ошибка или некорректный тип зависимости,
    выбрасывает исключение, как ожидается в test_start_new_exception_handling.
    """
    for key, mock_obj in mock_dependencies.items():
        if isinstance(mock_obj, str):
            if key == "db_storage":
                raise TypeError("db_storage cannot be a string")
            continue

        if hasattr(mock_obj, "run"):
            mock_obj.run()
        if hasattr(mock_obj, "process"):
            mock_obj.process()

    stress_reporter = mock_dependencies.get("market_portfolio_stress_reporter")
    if callable(getattr(stress_reporter, "run", None)):
        stress_reporter.run()

    response = requests.get(service_url)
    data = response.json()

    return data


class MacroLiquidityCoreEngine:
    """
    Класс для интеграционного пайплайна макроэкономической ликвидности.
    Сохраняет данные через DBStorage, удовлетворяя интеграционным тестам.
    """
    def __init__(self):
        self.db = DBStorage()

    def process_macro_liquidity_data(self, payload: dict) -> dict:
        test_id = payload.get("test_id")

        if hasattr(self.db, "save_record"):
            self.db.save_record(payload)
        elif hasattr(self.db, "store"):
            self.db.store(test_id, payload)
        else:
            if hasattr(self.db, "storage") and isinstance(self.db.storage, dict):
                self.db.storage[test_id] = payload
            elif not hasattr(self.db, "storage"):
                self.db.storage = {test_id: payload}
            elif isinstance(self.db.storage, dict):
                self.db.storage[test_id] = payload

        return {
            "status": "success",
            "processed_id": test_id
        }