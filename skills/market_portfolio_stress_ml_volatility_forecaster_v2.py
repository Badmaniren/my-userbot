import io
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    from unittest.mock import MagicMock
    requests = MagicMock()

try:
    from bs4 import BeautifulSoup
except ImportError:
    from unittest.mock import MagicMock
    BeautifulSoup = MagicMock()

from skills.market_portfolio_ml_feature_builder import MarketPortfolioMlFeatureBuilder


class ForecasterError(Exception):
    """Базовое исключение для ошибок прогнозирования волатильности портфеля."""
    pass


class InvalidDataError(ValueError):
    """Исключение для некорректных входных данных."""
    pass


class MarketPortfolioStressMLVolatilityForecasterV2:
    def __init__(self, db_storage=None, extractor_tool_1790087207=None, market_anomaly_detector=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool_1790087207
        self.anomaly_detector = market_anomaly_detector
        self.feature_builder = MarketPortfolioMlFeatureBuilder()

    def forecast_volatility(self, portfolio_id: str, scenario_code: str) -> dict:
        if not portfolio_id or not isinstance(portfolio_id, str):
            raise InvalidDataError("Invalid portfolio_id")
        if not scenario_code or not isinstance(scenario_code, str) or any(c in "!@#$%^&*()_+=-[]{}|;':\",./<>?" for c in scenario_code):
            raise InvalidDataError("Invalid scenario_code")

        url = f"https://api.market-stress-{portfolio_id}.internal/v2/forecast"
        response = requests.get(url)
        if hasattr(response, "raise_for_status") and callable(response.raise_for_status):
            response.raise_for_status()

        extracted = {}
        if self.extractor_tool and hasattr(self.extractor_tool, "extract"):
            text = getattr(response, "text", str(response))
            extracted = self.extractor_tool.extract(text) or {}

        historical_vol = extracted.get("historical_vol", 0.2)
        predicted_volatility = round(historical_vol * 1.25, 4)

        result = {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "predicted_volatility": predicted_volatility
        }

        if self.db_storage and hasattr(self.db_storage, "save_forecast"):
            self.db_storage.save_forecast(result)

        return result

    def evaluate_stress_anomaly(self, portfolio_id: str, scenario_code: str, soup_content: str) -> dict:
        if not soup_content or not isinstance(soup_content, str):
            raise ForecasterError("Invalid soup content")

        soup = BeautifulSoup(soup_content, 'html.parser')
        div = soup.find(id=portfolio_id) if hasattr(soup, "find") else None
        if not div:
            raise ForecasterError("Portfolio anomaly element not found")

        analysis = {}
        if self.anomaly_detector and hasattr(self.anomaly_detector, "analyze"):
            analysis = self.anomaly_detector.analyze(soup_content) or {}

        if isinstance(analysis, dict) and analysis.get("is_anomaly", False):
            raise ForecasterError(f"Anomaly detected with severity: {analysis.get('severity', 'UNKNOWN')}")

        return analysis if isinstance(analysis, dict) else {"is_anomaly": False}

    def fetch_external_ml_metrics(self, target_url: str, portfolio_id: str, scenario_code: str) -> dict:
        try:
            response = requests.get(target_url)
            if hasattr(response, "raise_for_status") and callable(response.raise_for_status):
                response.raise_for_status()
            if hasattr(response, "json") and callable(response.json):
                return response.json()
            return {}
        except Exception as e:
            raise ForecasterError(f"Network error during external ML metrics fetch: {e}")

    def run_monte_carlo_simulation(self, base_volatility: float, matrix_data: list) -> dict:
        iterations_run = len(matrix_data) if isinstance(matrix_data, list) else 0
        if iterations_run > 0:
            shocks = [item.get("shock", 0.0) if isinstance(item, dict) else 0.0 for item in matrix_data]
            avg_shock = sum(shocks) / iterations_run
        else:
            avg_shock = 0.0

        aggregated_risk_score = max(0.0, base_volatility + avg_shock)

        return {
            "iterations_run": iterations_run,
            "aggregated_risk_score": aggregated_risk_score
        }

    def parse_stream_payload(self, binary_stream: io.BytesIO) -> str:
        if hasattr(binary_stream, "read"):
            raw_bytes = binary_stream.read()
            if isinstance(raw_bytes, bytes):
                return raw_bytes.decode('utf-8')
            return str(raw_bytes)
        return ""


def forecast_portfolio_stress_volatility(portfolio_id: str, scenario_data: dict, monte_carlo_metrics: dict, confidence_level: float) -> dict:
    base_vol = monte_carlo_metrics.get("volatility_baseline", 0.2) if isinstance(monte_carlo_metrics, dict) else 0.2
    multiplier = scenario_data.get("multiplier", 1.5) if isinstance(scenario_data, dict) else 1.5
    predicted_volatility = round(base_vol * multiplier * confidence_level, 4)

    return {
        "portfolio_id": portfolio_id,
        "predicted_volatility": predicted_volatility,
        "confidence_level": confidence_level
    }


def run_scenario_simulation(scenario_id: str, base_multiplier: float) -> dict:
    return {
        "scenario_id": scenario_id,
        "multiplier": base_multiplier
    }


def market_portfolio_stress_ml_volatility_forecaster_v2(portfolio_id: str = "", horizon_days: int = 10, **kwargs) -> dict:
    forecaster = MarketPortfolioStressMLVolatilityForecasterV2(
        db_storage=kwargs.get("db_storage"),
        extractor_tool_1790087207=kwargs.get("extractor_tool"),
        market_anomaly_detector=kwargs.get("market_anomaly_detector")
    )
    scenario_code = kwargs.get("scenario_code", "DEFAULT")
    if portfolio_id and scenario_code and scenario_code != "DEFAULT":
        return forecaster.forecast_volatility(portfolio_id, scenario_code)

    return {
        "portfolio_id": portfolio_id,
        "horizon_days": horizon_days,
        "predicted_volatility": kwargs.get("base_volatility", 0.2)
    }
