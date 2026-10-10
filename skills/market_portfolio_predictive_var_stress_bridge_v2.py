from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine,
    VarEngineError,
    InsufficientDataError
)
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine


class BridgeExecutionError(Exception):
    """Исключение при ошибке выполнения пайплайна в бридже."""
    pass


class BridgeValidationError(Exception):
    """Исключение при ошибке валидации данных в бридже."""
    pass


class PredictiveVarStressBridgeV2:
    """
    Связующий модуль, объединяющий предиктивный VaR-движок и 
    сценарный стресс-тестировщик Монте-Карло.
    """

    def __init__(self, db_storage=None, extractor_tool=None, market_anomaly_detector=None,
                 var_engine=None, monte_carlo_engine=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector

        self.var_engine = var_engine or PredictiveVarEngine(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector
        )
        self.monte_carlo_engine = monte_carlo_engine or MonteCarloStressEngine()

    def execute_combined_risk_pipeline(self, portfolio_id: str, scenario_code: str,
                                       simulations: int, horizon_days: int,
                                       confidence_level: float, portfolio_value: float,
                                       scenario_params: dict, iterations: int) -> dict:
        """Выполняет объединенный пайплайн расчета VaR и стресс-тестирования Монте-Карло."""
        try:
            var_result = self.var_engine.calculate_predictive_var(
                portfolio_id=portfolio_id,
                portfolio_value=portfolio_value,
                horizon_days=horizon_days,
                confidence_level=confidence_level
            )
        except InsufficientDataError as e:
            raise BridgeValidationError(str(e))
        except VarEngineError as e:
            raise BridgeExecutionError(str(e))

        mc_result = self.monte_carlo_engine.run_simulation(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        return {
            "portfolio_id": portfolio_id,
            "predictive_var_metrics": var_result,
            "monte_carlo_metrics": mc_result
        }

    def execute_bridge_pipeline(self, portfolio_id: str, scenario_code: str,
                                portfolio_value: float, simulations: int,
                                horizon_days: int, confidence_level: float,
                                scenario_params: dict, iterations: int) -> dict:
        """Интеграционный метод выполнения пайплайна с расширенными метриками."""
        var_result = self.var_engine.calculate_predictive_var(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            horizon_days=horizon_days,
            confidence_level=confidence_level
        )
        mc_result = self.monte_carlo_engine.run_simulation(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        predictive_var_val = var_result.get("predictive_var", 0.0)
        monte_carlo_loss = mc_result.get("monte_carlo_stress_loss", 0.0)
        integrated_risk_score = round((predictive_var_val + monte_carlo_loss) / 2.0, 2)

        return {
            "portfolio_id": portfolio_id,
            "predictive_var": var_result,
            "monte_carlo_stress": mc_result,
            "integrated_risk_score": integrated_risk_score
        }

    def consume_and_bridge_stream(self, stream_source) -> dict:
        """Потребляет поток данных рынка и передает его в VaR-движок."""
        return self.var_engine.process_market_stream(stream_source)

    def export_combined_audit_report(self, report_id: str, loss_limit: float) -> dict:
        """Экспортирует объединенный аудиторский отчет."""
        var_audit = self.var_engine.export_predictive_audit_report(report_id, loss_limit)
        mc_audit = self.monte_carlo_engine.export_report(report_id, loss_limit)

        return {
            "report_id": report_id,
            "predictive_audit": var_audit,
            "monte_carlo_audit": mc_audit
        }

    def export_integrated_audit_report(self, report_id: str, loss_limit: float, metrics: dict) -> dict:
        """Экспортирует интегрированный отчет по результатам интеграционных тестов."""
        return {
            "report_id": report_id,
            "loss_limit": loss_limit,
            "metrics_summary": metrics,
            "status": "approved"
        }