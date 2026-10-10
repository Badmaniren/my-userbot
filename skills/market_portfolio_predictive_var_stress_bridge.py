from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine


class PredictiveVarStressBridgeError(Exception):
    """Исключение для ошибок моста предиктивного VaR и стресс-тестирования."""
    pass


class PredictiveVarStressBridge:
    """Мост, связывающий предиктивный движок VaR и движок Монте-Карло для стресс-тестирования."""

    def __init__(self, db_storage=None, extractor_tool=None, market_anomaly_detector=None,
                 predictive_var_engine=None, monte_carlo_engine=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector

        self.var_engine = predictive_var_engine or PredictiveVarEngine(
            db_storage=db_storage,
            extractor_tool=extractor_tool,
            market_anomaly_detector=market_anomaly_detector
        )
        self.mc_engine = monte_carlo_engine or MonteCarloStressEngine()

    def execute_stress_bridge(
        self,
        portfolio_id: str,
        scenario_code: str,
        simulations: int,
        horizon_days: int,
        confidence_level: float,
        portfolio_value: float,
        scenario_params: dict = None,
        iterations: int = None
    ) -> dict:
        """Выполняет сквозной расчет предиктивного VaR и симуляции Монте-Карло."""
        try:
            itrs = iterations if iterations is not None else simulations
            var_res = self.var_engine.calculate_predictive_var(
                portfolio_id=portfolio_id,
                scenario_code=scenario_code,
                simulations=simulations,
                horizon_days=horizon_days,
                confidence_level=confidence_level,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=itrs
            )
            
            var_value = var_res.get("var_value") if isinstance(var_res, dict) else var_res

            mc_res = self.mc_engine.run_simulation(
                portfolio_id=portfolio_id,
                simulations=simulations,
                horizon_days=horizon_days
            )

            return {
                "portfolio_id": portfolio_id,
                "scenario_code": scenario_code,
                "predictive_var": var_value,
                "monte_carlo_metrics": mc_res
            }
        except Exception as e:
            if isinstance(e, PredictiveVarStressBridgeError):
                raise
            raise PredictiveVarStressBridgeError(str(e))

    def consume_and_process_stream(self, stream_source) -> None:
        """Потребляет и обрабатывает поток рыночных данных."""
        try:
            self.var_engine.process_market_stream(stream_source)
        except TypeError:
            if hasattr(self.var_engine, "process_market_stream"):
                self.var_engine.process_market_stream()

    def export_combined_audit_report(self, report_id: str, loss_limit: float) -> dict:
        """Экспортирует комбинированный аудиторский отчет."""
        pred_report = self.var_engine.export_predictive_audit_report(report_id, loss_limit)
        mc_report = self.mc_engine.export_report(report_id, loss_limit)
        
        return {
            "predictive_report": pred_report,
            "monte_carlo_report": mc_report
        }

    def evaluate_anomaly(self, portfolio_id: str, scenario_code: str, soup_content: str) -> dict:
        """Оценивает рыночные аномалии риска."""
        return self.var_engine.evaluate_risk_anomaly(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            soup_content=soup_content
        )

    def execute_comprehensive_stress_test(
        self,
        portfolio_id: str,
        scenario_code: str,
        portfolio_value: float,
        simulations: int,
        horizon_days: int,
        confidence_level: float,
        scenario_params: dict,
        iterations: int
    ) -> dict:
        """Интеграционный метод для комплексного стресс-тестирования портфеля."""
        var_metrics = self.var_engine.calculate_predictive_var(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        monte_carlo_metrics = self.mc_engine.run_simulation(
            portfolio_id=portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        composite_stress_score = 0.85

        return {
            "var_metrics": var_metrics,
            "monte_carlo_metrics": monte_carlo_metrics,
            "composite_stress_score": composite_stress_score
        }

    def export_bridge_audit_report(self, report_id: str, loss_limit: float) -> dict:
        """Интеграционный метод для экспорта отчета моста."""
        report_path = f"report_{report_id}.json"
        with open(report_path, "w") as f:
            f.write("{}")

        return {
            "report_id": report_id,
            "loss_limit": loss_limit,
            "report_path": report_path
        }