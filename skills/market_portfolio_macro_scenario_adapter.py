import json
import uuid
import io
import requests
from bs4 import BeautifulSoup


class MacroScenarioAdapterException(Exception):
    """Custom exception for macro scenario adapter failures."""
    pass


class DBStorageHandler:
    def __init__(self):
        self._store = {}
        self.audit_logs = []
        self.error_logs = []

    def __call__(self, payload=None, **kwargs):
        if payload is None:
            payload = kwargs
        if isinstance(payload, str):
            return self._store.get(payload, {"run_id": payload})
        if not isinstance(payload, dict):
            return {}

        action = payload.get("action")
        run_id = payload.get("run_id")

        if action == "get":
            return self._store.get(run_id, {"run_id": run_id})
        elif action == "save" or run_id:
            if run_id:
                self._store[run_id] = payload
            return payload
        return {}

    def save_audit_log(self, payload=None, **kwargs):
        log = payload if payload is not None else kwargs
        self.audit_logs.append(log)
        return True

    def save_error_log(self, payload=None, **kwargs):
        log = payload if payload is not None else kwargs
        self.error_logs.append(log)
        return True

    def get_record(self, run_id):
        return self._store.get(run_id)

    def save_record(self, run_id, data):
        self._store[run_id] = data
        return True


db_storage = DBStorageHandler()


class DefaultExtractorTool:
    def fetch_factor(self, indicator: str) -> dict:
        return {"indicator": indicator, "value": 0.0}


class DefaultSimulator:
    def generate(self, portfolio_id, factors=None) -> dict:
        return {"scenario_id": str(uuid.uuid4()), "status": "adapted"}


class MarketPortfolioMacroScenarioAdapter:
    def __init__(self, db_storage=None, extractor_tool=None, market_scenario_simulator=None):
        self.db_storage = db_storage if db_storage is not None else globals()["db_storage"]
        self.extractor_tool = extractor_tool if extractor_tool is not None else DefaultExtractorTool()
        self.market_scenario_simulator = (
            market_scenario_simulator if market_scenario_simulator is not None else DefaultSimulator()
        )

    def adapt_factors(self, portfolio_id: str, macro_indicators: list) -> dict:
        if not isinstance(macro_indicators, list):
            macro_indicators = [macro_indicators]

        extracted_factors = []
        for indicator in macro_indicators:
            try:
                factor_data = self.extractor_tool.fetch_factor(indicator)
                extracted_factors.append(factor_data)
            except Exception as e:
                if hasattr(self.db_storage, "save_error_log"):
                    self.db_storage.save_error_log({"portfolio_id": portfolio_id, "error": str(e)})
                raise MacroScenarioAdapterException(f"Failed to fetch macro factor '{indicator}': {str(e)}") from e

        try:
            if hasattr(self.market_scenario_simulator, "generate"):
                sim_result = self.market_scenario_simulator.generate(portfolio_id, extracted_factors)
            elif callable(self.market_scenario_simulator):
                sim_result = self.market_scenario_simulator({"portfolio_id": portfolio_id, "factors": extracted_factors})
            else:
                sim_result = {"scenario_id": str(uuid.uuid4()), "status": "adapted"}

            if hasattr(self.db_storage, "save_audit_log"):
                scenario_id = sim_result.get("scenario_id") if isinstance(sim_result, dict) else None
                self.db_storage.save_audit_log({
                    "action": "adapt_factors",
                    "portfolio_id": portfolio_id,
                    "scenario_id": scenario_id
                })

            return sim_result
        except MacroScenarioAdapterException:
            raise
        except Exception as e:
            if hasattr(self.db_storage, "save_error_log"):
                self.db_storage.save_error_log({"portfolio_id": portfolio_id, "error": str(e)})
            raise MacroScenarioAdapterException(f"Failed to generate scenario: {str(e)}") from e

    def parse_external_feed(self, url: str, tag: str):
        try:
            response = requests.get(url, stream=True, timeout=10)
            if hasattr(response.raw, "read"):
                content = response.raw.read()
            else:
                content = response.content
            if isinstance(content, bytes):
                content_str = content.decode("utf-8", errors="ignore")
            else:
                content_str = str(content)

            soup = BeautifulSoup(content_str, "html.parser")
            element = soup.find(tag)
            if element:
                return element.text
            return content_str
        except MacroScenarioAdapterException:
            raise
        except Exception as e:
            raise MacroScenarioAdapterException(f"Failed to parse feed at {url}: {str(e)}") from e

    def _compute_internal_stress(self, portfolio_id: str, inflation: float, interest_rate: float) -> float:
        return round(abs(float(inflation) * 2.5 + float(interest_rate) * 1.5), 2)

    def evaluate_macro_stress(self, portfolio_id: str, inflation: float, interest_rate: float) -> float:
        return self._compute_internal_stress(portfolio_id, inflation, interest_rate)


def market_portfolio_macro_scenario_adapter(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}
    run_id = payload.get("run_id", str(uuid.uuid4()))
    simulation_result = payload.get("simulation_result", {})
    scenario_id = simulation_result.get("scenario_id") if isinstance(simulation_result, dict) else None

    result = {
        "run_id": run_id,
        "success": True,
        "persisted": True,
        "scenario_id": scenario_id,
        "simulation_result": simulation_result,
        "macro_factors": payload.get("macro_factors", {})
    }

    db_storage({"action": "save", "run_id": run_id, "data": result, **result})

    export_filename = f"macro_report_{run_id}.json"
    try:
        with open(export_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except OSError as e:
        if hasattr(db_storage, "save_error_log"):
            db_storage.save_error_log({"run_id": run_id, "error": str(e)})

    return result


def market_news_sentiment_analyzer(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}
    run_id = payload.get("run_id")
    metric = payload.get("metric", "unknown")
    val = float(payload.get("value", 0.0))
    rate = float(payload.get("rate", 0.0))

    sentiment = "bullish" if val > 0 else ("bearish" if val < 0 else "neutral")
    return {
        "run_id": run_id,
        "metric": metric,
        "value": val,
        "rate": rate,
        "sentiment": sentiment,
        "score": val
    }


def market_portfolio_scenario_simulator(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}
    run_id = payload.get("run_id")
    scenario_id = str(uuid.uuid4())
    return {
        "scenario_id": scenario_id,
        "run_id": run_id,
        "status": "simulated",
        "sentiment_data": payload.get("sentiment_data"),
        "shock_multiplier": payload.get("shock_multiplier", 1.0)
    }
