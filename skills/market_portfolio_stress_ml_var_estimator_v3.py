from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import market_portfolio_stress_ml_volatility_forecaster_v2
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage

class VaREestimationError(Exception):
    """Исключение, возникающее при ошибке оценки VaR."""
    pass

class InsufficientDataError(Exception):
    """Исключение, возникающее при недостаточном количестве данных для анализа."""
    pass


class MLVaREstimatorV3:
    def __init__(self, volatility_forecaster=None, monte_carlo_engine=None, db_storage=None):
        self.volatility_forecaster = volatility_forecaster
        self.monte_carlo_engine = monte_carlo_engine
        self.db_storage = db_storage

    def calculate_var(self, portfolio_id, weights, returns, confidence, horizon):
        if not returns or len(returns) < 5:
            raise InsufficientDataError("Insufficient historical returns data provided.")

        try:
            predicted_volatility = self.volatility_forecaster.predict_volatility(
                portfolio_id=portfolio_id,
                weights=weights,
                returns=returns,
                confidence=confidence,
                horizon=horizon
            )

            var_value = self.monte_carlo_engine.simulate_tail_risk(
                weights=weights,
                returns=returns,
                volatility=predicted_volatility,
                confidence=confidence,
                horizon=horizon
            )
        except Exception as e:
            if isinstance(e, InsufficientDataError):
                raise e
            raise VaREestimationError(f"Failed to calculate ML VaR: {str(e)}")

        result = {
            "portfolio_id": portfolio_id,
            "var_value": var_value,
            "predicted_volatility": predicted_volatility,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.db_storage is not None:
            self.db_storage.save_estimate(result)

        return result

    def parse_external_market_stream(self, stream):
        return stream.read()

    def fetch_external_benchmark(self, url):
        if requests is None:
            raise VaREestimationError("requests package is required for fetch_external_benchmark")
        response = requests.get(url, timeout=10)
        return response.json()

    def extract_anomaly_metric(self, soup_obj, class_name):
        if soup_obj is None:
            return None
        element = soup_obj.find(class_=class_name)
        if element:
            return element.text.strip()
        return None


def market_portfolio_stress_ml_var_estimator_v3(payload):
    portfolio_id = payload.get("portfolio_id")
    confidence_level = payload.get("confidence_level", 0.95)
    volatility_forecast = payload.get("volatility_forecast", 0.2)
    base_value = payload.get("base_value", 100000.0)

    if isinstance(volatility_forecast, list):
        vol = round(sum(volatility_forecast) / len(volatility_forecast), 6) if volatility_forecast else 0.2
    else:
        vol = float(volatility_forecast)

    var_value = base_value * vol * 1.645

    result = {
        "portfolio_id": portfolio_id,
        "var_value": float(var_value),
        "predicted_volatility": float(vol),
        "timestamp": datetime.utcnow().isoformat()
    }

    from skills import db_storage as db_storage_module
    target_db = getattr(db_storage_module, "db_storage", db_storage)
    target_db({
        "action": "save",
        "table": "portfolio_var_evaluations",
        "portfolio_id": portfolio_id,
        "data": result
    })

    return result