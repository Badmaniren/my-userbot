from typing import Dict, Any, Optional
from skills.market_portfolio_ml_stress_evaluator import (
    MarketPortfolioMLStressEvaluator,
    StressEvaluationError
)
from skills.market_portfolio_stress_auto_rebalance_trigger import (
    StressAutoRebalanceTrigger
)


class AdaptiveAllocationError(Exception):
    """Исключение, возникающее при ошибках адаптивного распределения активов."""
    pass


class MLStressAdaptiveAllocator:
    """
    Связывает предиктивный ML-оценщик стресс-рисков и систему автоматического
    ребалансирования в единый адаптивный контур защиты портфеля.
    """

    def __init__(
        self,
        db_storage: Any = None,
        extractor_tool: Any = None,
        market_anomaly_detector: Any = None,
        window_size: int = 30
    ) -> None:
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector
        self.window_size = window_size

        self.ml_evaluator = MarketPortfolioMLStressEvaluator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            window_size=self.window_size
        )
        self.rebalance_trigger = StressAutoRebalanceTrigger()

    def evaluate_and_adapt(
        self,
        portfolio_id: str,
        prices: list,
        scenario_code: str,
        confidence_level: float,
        threshold: float
    ) -> Dict[str, Any]:
        """Оценивает стресс-риск портфеля и запускает триггер ребалансировки."""
        try:
            stress_evaluation = self.ml_evaluator.evaluate_stress(
                portfolio_id, prices, scenario_code, confidence_level
            )
        except StressEvaluationError as e:
            raise AdaptiveAllocationError(str(e)) from e

        rebalance_trigger = self.rebalance_trigger.evaluate_and_trigger(
            portfolio_id, threshold
        )

        return {
            "stress_evaluation": stress_evaluation,
            "rebalance_trigger": rebalance_trigger
        }

    def process_external_feed_and_allocate(
        self,
        target_url: str,
        portfolio_id: str,
        scenario_code: str
    ) -> Dict[str, Any]:
        """Обрабатывает внешний фид стресс-данных и адаптирует распределение."""
        feed_data = self.rebalance_trigger.fetch_external_stress_feed(target_url)
        parsed_stream = self.ml_evaluator.parse_external_stream(feed_data)

        return {
            "parsed_stream": parsed_stream,
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code
        }

    def notify_allocation_audit(self, alert_id: str, message: str) -> Dict[str, Any]:
        """Отправляет уведомление в систему аудита адаптивного действия."""
        return self.rebalance_trigger.notify_audit_system(alert_id, message)

    def execute_adaptive_allocation(
        self,
        portfolio_id: str,
        prices: list,
        scenario_code: str,
        confidence_level: float,
        threshold: float
    ) -> Dict[str, Any]:
        """Метод для совместимости с интеграционными тестами."""
        result = self.evaluate_and_adapt(
            portfolio_id=portfolio_id,
            prices=prices,
            scenario_code=scenario_code,
            confidence_level=confidence_level,
            threshold=threshold
        )
        return {
            "portfolio_id": portfolio_id,
            "result": result
        }


class AdaptiveStressAllocator(MLStressAdapterAlias := MLStressAdaptiveAllocator):
    """Алиас класса для прохождения интеграционных тестов."""
    pass