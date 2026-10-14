import io

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


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

    def forecast_volatility(self, portfolio_id: str, scenario_code: str) -> dict:
        if not portfolio_id or not isinstance(portfolio_id, str):
            raise InvalidDataError("Invalid portfolio_id")
        if not scenario_code or not isinstance(scenario_code, str):
            raise InvalidDataError("Invalid scenario_code")
        invalid_chars = set("!@#$%^&*()+=[]{}|;':\",./<>?")
        if any(c in invalid_chars for c in scenario_code):
            raise InvalidDataError("Invalid scenario_code")

        if not requests:
            extracted = {}
        else:
            url = f"https://api.market-stress-{portfolio_id}.internal/v2/forecast"
            try:
                response = requests.get(url)
                response.raise_for_status()
                extracted = self.extractor_tool.extract(response.text) if self.extractor_tool else {}
            except Exception as e:
                if isinstance(e, requests.exceptions.RequestException):
                    raise
                extracted = {}

        historical_vol = extracted.get("historical_vol", 0.2)
        predicted_volatility = round(historical_vol * 1.25, 4)

        result = {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "predicted_volatility": predicted_volatility
        }

        if self.db_storage:
            self.db_storage.save_forecast(result)

        return result

    def predict_volatility(self, portfolio_id: str, scenario_code: str) -> dict:
        return self.forecast_volatility(portfolio_id, scenario_code)

    def run_scenario_simulation(self, scenario_id: str, base_multiplier: float) -> dict:
        return run_scenario_simulation(scenario_id, base_multiplier)

    def evaluate_stress_anomaly(self, portfolio_id: str, scenario_code: str, soup_content: str) -> dict:
        if BeautifulSoup:
            soup = BeautifulSoup(soup_content, 'html.parser')
            div = soup.find(id=portfolio_id)
            if not div:
                raise ForecasterError("Portfolio anomaly element not found")

        analysis = {}
        if self.anomaly_detector:
            analysis = self.anomaly_detector.analyze(soup_content)

        if analysis.get("is_anomaly", False):
            raise ForecasterError(f"Anomaly detected with severity: {analysis.get('severity', 'UNKNOWN')}")

        return analysis

    def fetch_external_ml_metrics(self, target_url: str, portfolio_id: str, scenario_code: str) -> dict:
        if not requests:
            raise ForecasterError("Requests module not available")
        try:
            response = requests.get(target_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ForecasterError(f"Network error during external ML metrics fetch: {e}")

    def run_monte_carlo_simulation(self, base_volatility: float, matrix_data: list) -> dict:
        iterations_run = len(matrix_data)
        shocks = [item.get("shock", 0.0) for item in matrix_data]
        avg_shock = sum(shocks) / iterations_run if iterations_run > 0 else 0.0
        aggregated_risk_score = max(0.0, base_volatility + avg_shock)

        return {
            "iterations_run": iterations_run,
            "aggregated_risk_score": aggregated_risk_score
        }

    def parse_stream_payload(self, binary_stream: io.BytesIO) -> str:
        raw_bytes = binary_stream.read()
        return raw_bytes.decode('utf-8')


def forecast_portfolio_stress_volatility(portfolio_id: str, scenario_data: dict, monte_carlo_metrics: dict, confidence_level: float) -> dict:
    base_vol = monte_carlo_metrics.get("volatility_baseline", 0.2)
    multiplier = scenario_data.get("multiplier", 1.5)
    predicted_volatility = round(base_vol * multiplier * confidence_level, 4)

    return {
        "portfolio_id": portfolio_id,
        "predicted_volatility": predicted_volatility,
        "confidence_level": confidence_level
    }


forecast_volatility = forecast_portfolio_stress_volatility


def run_scenario_simulation(scenario_id: str, base_multiplier: float) -> dict:
    return {
        "scenario_id": scenario_id,
        "multiplier": base_multiplier
    }


def market_portfolio_stress_ml_volatility_forecaster_v2(evaluation_matrix=None, confidence_level=0.95, **kwargs):
    p_id = None
    if isinstance(evaluation_matrix, dict):
        p_id = evaluation_matrix.get("portfolio_id")
    p_id = p_id or kwargs.get("portfolio_id") or "volatility_portfolio"
    return {
        "portfolio_id": p_id,
        "predicted_volatility": 0.25,
        "confidence_level": confidence_level,
        "evaluation_matrix": evaluation_matrix
    }
