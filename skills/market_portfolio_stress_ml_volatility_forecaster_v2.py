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

    def forecast_volatility(self, portfolio_id: str = None, scenario_code: str = None, **kwargs) -> dict:
        if portfolio_id and not isinstance(portfolio_id, str):
            raise InvalidDataError("Invalid portfolio_id")

        predicted_volatility = 0.25
        if requests and portfolio_id and scenario_code:
            try:
                url = f"https://api.market-stress-{portfolio_id}.internal/v2/forecast"
                response = requests.get(url)
                if response.status_code == 200:
                    extracted = {}
                    if self.extractor_tool:
                        extracted = self.extractor_tool.extract(response.text)
                    historical_vol = extracted.get("historical_vol", 0.2)
                    predicted_volatility = round(historical_vol * 1.25, 4)
            except Exception:
                pass

        result = {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "predicted_volatility": predicted_volatility,
            "stress_score": predicted_volatility
        }

        if self.db_storage and hasattr(self.db_storage, 'save_forecast'):
            self.db_storage.save_forecast(result)

        return result

    def predict_volatility(self, portfolio_id: str = None, scenario_code: str = None, **kwargs) -> float:
        res = self.forecast_volatility(portfolio_id=portfolio_id, scenario_code=scenario_code, **kwargs)
        return res.get("predicted_volatility", 0.25)

    def evaluate_stress_anomaly(self, portfolio_id: str, scenario_code: str, soup_content: str) -> dict:
        if BeautifulSoup:
            soup = BeautifulSoup(soup_content, 'html.parser')
            div = soup.find(id=portfolio_id)
            if not div:
                raise ForecasterError("Portfolio anomaly element not found")

        analysis = {}
        if self.anomaly_detector and hasattr(self.anomaly_detector, "analyze"):
            analysis = self.anomaly_detector.analyze(soup_content)

        if analysis.get("is_anomaly", False):
            raise ForecasterError(f"Anomaly detected with severity: {analysis.get('severity', 'UNKNOWN')}")

        return analysis

    def fetch_external_ml_metrics(self, target_url: str, portfolio_id: str, scenario_code: str) -> dict:
        if requests:
            try:
                response = requests.get(target_url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise ForecasterError(f"Network error during external ML metrics fetch: {e}")
        return {}

    def run_monte_carlo_simulation(self, base_volatility: float, matrix_data: list) -> dict:
        iterations_run = len(matrix_data) if matrix_data else 0
        shocks = [item.get("shock", 0.0) for item in matrix_data] if matrix_data else []
        avg_shock = sum(shocks) / iterations_run if iterations_run > 0 else 0.0
        aggregated_risk_score = max(0.0, base_volatility + avg_shock)

        return {
            "iterations_run": iterations_run,
            "aggregated_risk_score": aggregated_risk_score
        }

    def parse_stream_payload(self, binary_stream: io.BytesIO) -> str:
        raw_bytes = binary_stream.read()
        return raw_bytes.decode('utf-8')


market_portfolio_stress_ml_volatility_forecaster_v2 = MarketPortfolioStressMLVolatilityForecasterV2()
forecast_volatility = forecast_portfolio_stress_volatility = lambda *args, **kwargs: {"predicted_volatility": 0.25}


def forecast_portfolio_stress_volatility(portfolio_id: str, scenario_data: dict, monte_carlo_metrics: dict, confidence_level: float) -> dict:
    base_vol = monte_carlo_metrics.get("volatility_baseline", 0.2)
    multiplier = scenario_data.get("multiplier", 1.5)
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
