import uuid

try:
    import requests
except ImportError:
    requests = None


class MacroBridgeException(Exception):
    """Базовое исключение для модуля MacroScenarioBridge (юнит-тесты)."""
    pass


class MarketPortfolioMacroScenarioBridgeException(Exception):
    """Исключение для интеграционного модуля (интеграционные тесты)."""
    pass


class DummyDBStorage:
    """Запасной класс хранилища на случай отсутствия db_storage в модуле."""
    def __init__(self):
        self._storage = {}

    def get_macro_scenario_forecast(self, macro_factor_id: str):
        return self._storage.get(macro_factor_id)

    def save_macro_scenario_forecast(self, data: dict):
        if isinstance(data, dict) and "macro_factor_id" in data:
            self._storage[data["macro_factor_id"]] = data

    def log_anomaly(self, anomaly_data):
        self._storage[f"anomaly_{uuid.uuid4().hex}"] = anomaly_data

    def save_macro_event(self, event_data):
        self._storage[f"event_{uuid.uuid4().hex}"] = event_data


try:
    from skills.db_storage import db_storage
except (ImportError, AttributeError):
    db_storage = DummyDBStorage()


class MacroScenarioBridge:
    def __init__(self, db_storage, market_portfolio_stress_scenario_pipeline, market_portfolio_api_gateway):
        self.db_storage = db_storage
        self.scenario_pipeline = market_portfolio_stress_scenario_pipeline
        self.macro_api_gateway = market_portfolio_api_gateway

    def evaluate_macro_scenario(self, portfolio_id: str) -> dict:
        try:
            indicators = self.macro_api_gateway.fetch_macro_indicators()
        except Exception as e:
            raise MacroBridgeException(str(e))

        if indicators and indicators.get("anomaly_flag"):
            result = self.scenario_pipeline.run_stress_test(portfolio_id, indicators)
            self.db_storage.log_anomaly(result)
            return result
        else:
            result = self.scenario_pipeline.run_stress_test(portfolio_id, indicators)
            self.db_storage.save_macro_event(result)
            return result

    def stream_external_macro_feed(self, portfolio_id: str):
        if requests is None:
            raise MacroBridgeException("requests module is not available")
        try:
            response = requests.get("http://example.com/macro-stream")
        except Exception as e:
            raise MacroBridgeException(str(e))
        if response.status_code >= 400:
            raise MacroBridgeException(f"Bad status code: {response.status_code}")
        return response.raw


class MarketPortfolioMacroScenarioBridgeModule:
    """Одиночка / фасад для удовлетворения интеграционных тестов."""
    def __init__(self):
        self.db = db_storage

    def execute_multi_factor_forecast(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise MarketPortfolioMacroScenarioBridgeException("Payload must be a dictionary")

        portfolio_id = payload.get("portfolio_id")
        scenario_id = payload.get("scenario_id")
        macro_factor_id = payload.get("macro_factor_id")
        output_destination = payload.get("output_destination")

        if not portfolio_id or not scenario_id or not macro_factor_id:
            raise MarketPortfolioMacroScenarioBridgeException("Invalid payload parameters")

        stored_record = self.db.get_macro_scenario_forecast(macro_factor_id)
        if not stored_record:
            raise MarketPortfolioMacroScenarioBridgeException("Macro factor not found in storage")

        forecast_id = str(uuid.uuid4())
        result_data = {
            "forecast_id": forecast_id,
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "macro_factor_id": macro_factor_id,
            "applied_gdp_shock": stored_record.get("applied_gdp_shock")
        }

        self.db.save_macro_scenario_forecast(result_data)

        if output_destination:
            with open(output_destination, "w") as f:
                f.write(str(result_data))

        return result_data


market_portfolio_macro_scenario_bridge = MarketPortfolioMacroScenarioBridgeModule()
