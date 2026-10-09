import math
from typing import Any, Dict, List, Optional

from skills.market_portfolio_ml_feature_builder import (
    InsufficientDataError,
    MarketPortfolioMLFeatureBuilder,
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    MarketPortfolioStressMLVolatilityForecasterV2,
)


class StressEvaluationError(Exception):
    """Raised when stress evaluation fails."""
    pass


class InsufficientFeatureDataError(Exception):
    """Raised when feature builder has insufficient data."""
    pass


class MarketPortfolioMLStressEvaluator:
    def __init__(
        self,
        db_storage: Any = None,
        extractor_tool: Any = None,
        market_anomaly_detector: Any = None,
        window_size: int = 10,
    ):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector
        self.window_size = window_size

        self.feature_builder = MarketPortfolioMLFeatureBuilder()
        self.volatility_forecaster = MarketPortfolioStressMLVolatilityForecasterV2()

    def evaluate_portfolio_stress_resilience(
        self,
        portfolio_id: str,
        scenario_code: str,
        source_url: str,
    ) -> Dict[str, Any]:
        feature_builder_cls = MarketPortfolioMLFeatureBuilder
        volatility_forecaster_cls = MarketPortfolioStressMLVolatilityForecasterV2

        fb = feature_builder_cls()
        vf = volatility_forecaster_cls()

        try:
            features = fb.build_full_feature_vector_from_source(source_url)
        except InsufficientDataError as err:
            raise InsufficientFeatureDataError(str(err)) from err

        forecast = vf.forecast_volatility(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            features=features,
        )

        stress_score = forecast.get("stress_score", 0.0)

        return {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "stress_score": stress_score,
            "features": features,
            "forecast": forecast,
        }

    def evaluate_stress(
        self,
        portfolio_id: str,
        prices: List[float],
        scenario_code: str,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        if not (0.0 < confidence_level < 1.0):
            raise ValueError(f"Confidence level must be strictly between 0 and 1, got {confidence_level}")

        if len(prices) < self.window_size or len(prices) < 3:
            raise InsufficientDataError("Insufficient price data points for stress evaluation.")

        returns: List[float] = []
        for i in range(1, len(prices)):
            if prices[i - 1] <= 0 or prices[i] <= 0:
                ret = 0.0
            else:
                ret = math.log(prices[i] / prices[i - 1])
            returns.append(ret)

        n = len(returns)
        mean_ret = sum(returns) / n
        variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1) if n > 1 else 0.0
        std_ret = math.sqrt(variance)

        annualized_vol = std_ret * math.sqrt(252)

        peak = prices[0]
        max_drawdown = 0.0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak if peak > 0 else 0.0
            if dd > max_drawdown:
                max_drawdown = dd

        var_alpha = mean_ret - (1.645 if confidence_level <= 0.95 else 2.326) * std_ret

        features = {
            "log_returns_count": n,
            "mean_return": mean_ret,
            "volatility": std_ret,
            "annualized_volatility": annualized_vol,
            "max_drawdown": max_drawdown,
            "var": var_alpha,
        }

        forecasted_volatility = annualized_vol * 1.2
        vf_result = {
            "forecasted_volatility": forecasted_volatility,
            "confidence_level": confidence_level,
        }

        deep_dd_prob = min(1.0, max(0.0, max_drawdown * 1.5 + (0.5 * std_ret)))
        resilience_score = max(0.0, min(100.0, 100.0 * (1.0 - deep_dd_prob)))

        return {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "resilience_score": resilience_score,
            "deep_drawdown_probability": deep_dd_prob,
            "features": features,
            "volatility_forecast": vf_result,
        }

    def calculate_deep_drawdown_probability(
        self,
        base_volatility: float,
        matrix_data: List[List[float]],
    ) -> Dict[str, Any]:
        return self.volatility_forecaster.run_monte_carlo_simulation(base_volatility, matrix_data)

    def parse_external_stream(self, stream: Any) -> str:
        return self.volatility_forecaster.parse_stream_payload(stream)

    def get_external_metrics(
        self,
        target_url: str,
        portfolio_id: str,
        scenario_code: str,
    ) -> Dict[str, Any]:
        return self.volatility_forecaster.fetch_external_ml_metrics(
            target_url,
            portfolio_id,
            scenario_code,
        )


def evaluate_portfolio_stress(
    portfolio_id: str,
    prices: List[float],
    scenario_code: str,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    evaluator = MarketPortfolioMLStressEvaluator()
    return evaluator.evaluate_stress(
        portfolio_id=portfolio_id,
        prices=prices,
        scenario_code=scenario_code,
        confidence_level=confidence_level,
    )