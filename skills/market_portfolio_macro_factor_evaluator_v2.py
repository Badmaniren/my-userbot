import os
import json
import requests
from skills import market_anomaly_detector


class MacroFactorEvaluationError(Exception):
    """Custom exception for macro factor evaluation errors."""
    pass


class MacroDataFetchError(Exception):
    """Custom exception for macro factor data fetching errors."""
    pass


class MarketPortfolioMacroFactorEvaluatorV2:
    def __init__(
        self,
        db_storage=None,
        extractor_tool_1790087207=None,
        extractor_tool_1790102839=None,
        **kwargs
    ):
        self.db_storage = db_storage
        self.extractor_tool_1790087207 = extractor_tool_1790087207
        self.extractor_tool_1790102839 = extractor_tool_1790102839
        for key, value in kwargs.items():
            setattr(self, key, value)

    def evaluate_portfolio(self, portfolio_id: str, factors: list = None) -> dict:
        if factors is None:
            factors = []
        evaluation_results = {}
        try:
            for factor in factors:
                factor_data = {}
                if self.extractor_tool_1790087207 and hasattr(self.extractor_tool_1790087207, "fetch_factor"):
                    factor_data = self.extractor_tool_1790087207.fetch_factor(factor)
                impact = 0.0
                if self.extractor_tool_1790102839 and hasattr(self.extractor_tool_1790102839, "calculate_impact"):
                    impact = self.extractor_tool_1790102839.calculate_impact(factor_data)
                evaluation_results[factor] = impact
        except requests.RequestException as exc:
            if self.db_storage and hasattr(self.db_storage, "log_error"):
                self.db_storage.log_error(f"Network error evaluating factor for portfolio {portfolio_id}: {exc}")
            raise MacroFactorEvaluationError(f"Network error for portfolio {portfolio_id}: {exc}") from exc
        except Exception as exc:
            if self.db_storage and hasattr(self.db_storage, "log_error"):
                self.db_storage.log_error(f"Error evaluating factors for portfolio {portfolio_id}: {exc}")
            raise MacroFactorEvaluationError(f"Evaluation error for portfolio {portfolio_id}: {exc}") from exc

        result = {
            "portfolio_id": portfolio_id,
            "factors": evaluation_results,
            "status": "success"
        }
        if self.db_storage and hasattr(self.db_storage, "save_evaluation"):
            self.db_storage.save_evaluation(portfolio_id, result)

        return result

    def process_stream_feed(self, url: str) -> bool:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            if hasattr(response.raw, "read"):
                _ = response.raw.read()
            return True
        return False

    def check_anomalies(self, portfolio_id: str) -> dict:
        return market_anomaly_detector.analyze(portfolio_id)


def evaluate_macro_factors(data=None, **kwargs) -> dict:
    if isinstance(data, dict):
        payload = {**data, **kwargs}
    elif data is not None:
        payload = {"portfolio_id": str(data), **kwargs}
    else:
        payload = kwargs

    portfolio_id = payload.get("portfolio_id", "default_portfolio")
    gdp_growth = payload.get("gdp_growth", 0.0)
    inflation_rate = payload.get("inflation_rate", 0.0)
    interest_rate = payload.get("interest_rate", 0.0)

    macro_score = round((gdp_growth * 0.4) - (inflation_rate * 0.3) - (interest_rate * 0.3), 4)

    result = {
        "status": "success",
        "portfolio_id": portfolio_id,
        "macro_score": macro_score,
        "gdp_growth": gdp_growth,
        "inflation_rate": inflation_rate,
        "interest_rate": interest_rate,
        "factor_name": payload.get("factor_name", "macro_index"),
        "simulated_impact": payload.get("simulated_impact", macro_score)
    }

    return result


def save_macro_evaluation(data: dict):
    return True


def get_macro_evaluation(portfolio_id: str) -> dict:
    return {"portfolio_id": portfolio_id, "status": "success"}
