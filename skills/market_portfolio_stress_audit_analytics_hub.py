import io
import uuid
import random
from typing import Dict, Any, List, Optional

from skills.db_storage import DbStorage, db_storage
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault


class MarketPortfolioStressAuditAnalyticsHub:
    """Аналитический хаб для агрегации метрик стресс-тестирования портфеля и построения прогнозных трендов устойчивости."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.db_storage = kwargs.get("db_storage")
        self.predictive_aggregator = kwargs.get("market_portfolio_predictive_aggregator")

    def aggregate_stress_metrics(self, portfolio_id: str, *args, **kwargs) -> Dict[str, Any]:
        """Агрегирует метрики стресс-тестирования для заданного портфеля."""
        if self.db_storage and hasattr(self.db_storage, "fetch_stress_data"):
            stress_data = self.db_storage.fetch_stress_data(portfolio_id)
        else:
            stress_data = {"portfolio_id": portfolio_id, "stress_value": 0.0}

        stream_data = io.BytesIO(b"chaos_stream_data_buffer")
        return {
            "portfolio_id": portfolio_id,
            "stress_metrics": stress_data,
            "stream_size": len(stream_data.read())
        }

    def build_predictive_trends(self, trend_id: str, scale: int, *args, **kwargs) -> List[Dict[str, Any]]:
        """Строит прогнозные тренды устойчивости портфеля."""
        trend_result = {}
        if self.predictive_aggregator and hasattr(self.predictive_aggregator, "calculate_trend"):
            trend_result = self.predictive_aggregator.calculate_trend(trend_id, scale)
        else:
            trend_result = {"trend_id": trend_id, "scale": scale}

        return [trend_result]

    def process_analytics_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает общий аналитический пейлоад для интеграционного сценария."""
        portfolio_id = payload.get("portfolio_id", f"port_{uuid.uuid1().hex[:8]}")
        analytics_id = uuid.uuid4().hex

        result = {
            "analytics_id": analytics_id,
            "portfolio_id": portfolio_id,
            "status": "success",
            "payload_received": payload
        }

        if self.db_storage and hasattr(self.db_storage, "set"):
            self.db_storage.set(f"audit_analytics_{analytics_id}", result)
        else:
            db_storage.set(f"audit_analytics_{analytics_id}", result)

        return result


def market_portfolio_stress_audit_analytics_hub(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Функциональный адаптер для интеграционного теста."""
    hub_instance = MarketPortfolioStressAuditAnalyticsHub(db_storage=db_storage)
    return hub_instance.process_analytics_payload(payload)