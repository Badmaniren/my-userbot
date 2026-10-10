from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine, VarEngineError, InsufficientDataError
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync


class PredictiveVarHedgeSynthesizer:
    def __init__(
        self,
        db_storage=None,
        extractor_tool=None,
        market_anomaly_detector=None,
        monitor=None,
        evaluator=None,
        rebalancer=None,
        storage_file=None,
        advisor=None,
        pipeline=None,
        var_engine=None,
        auto_hedge_sync=None
    ):
        if var_engine is not None:
            self.var_engine = var_engine
        else:
            self.var_engine = PredictiveVarEngine(
                db_storage,
                extractor_tool,
                market_anomaly_detector
            )

        effective_storage = storage_file or db_storage or "market_data.db"
        if auto_hedge_sync is not None:
            self.auto_hedge_sync = auto_hedge_sync
        else:
            self.auto_hedge_sync = MarketPortfolioStressAutoHedgeSync(
                db_storage,
                monitor,
                evaluator,
                rebalancer,
                effective_storage,
                advisor,
                pipeline
            )

    def synthesize_and_execute_hedge(
        self,
        portfolio_id,
        scenario_code,
        simulations,
        horizon_days,
        confidence_level,
        portfolio_value,
        scenario_params,
        iterations,
        request_id,
        symbol,
        percentage,
        shifts
    ):
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

        hedge_result = self.auto_hedge_sync.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        return {
            "portfolio_id": portfolio_id,
            "var_metrics": var_metrics,
            "hedge_result": hedge_result
        }

    def synthesize_stress_var_and_hedge(
        self,
        portfolio_id,
        portfolio_value,
        scenario_params,
        confidence_level,
        horizon_days,
        iterations,
        request_id,
        symbol,
        percentage,
        shifts
    ):
        stress_var_metrics = self.var_engine.calculate_predictive_stress_var(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

        hedge_result = self.auto_hedge_sync.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        return {
            "portfolio_id": portfolio_id,
            "stress_var_metrics": stress_var_metrics,
            "hedge_result": hedge_result
        }

    def process_stream_and_auto_hedge(
        self,
        stream_mock,
        portfolio_id,
        request_id,
        symbol,
        percentage,
        shifts
    ):
        stream_response = self.var_engine.process_market_stream(stream_mock)

        hedge_result = self.auto_hedge_sync.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        return {
            "portfolio_id": portfolio_id,
            "stream_response": stream_response,
            "hedge_result": hedge_result
        }

    def synthesize_and_simulate(
        self,
        portfolio_id,
        scenario_code,
        request_id,
        symbol,
        percentage,
        portfolio_value,
        simulations,
        horizon_days,
        confidence_level,
        scenario_params,
        iterations,
        shifts
    ):
        try:
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
        except Exception:
            var_metrics = {
                "portfolio_id": portfolio_id,
                "predictive_var": 0.0,
                "confidence": confidence_level,
                "scenario_code": scenario_code
            }

        hedge_result = self.auto_hedge_sync.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        hedge_status = hedge_result.get("status", "SYNCHRONIZED") if isinstance(hedge_result, dict) else "SYNCHRONIZED"

        return {
            "portfolio_id": portfolio_id,
            "var_metrics": var_metrics,
            "hedge_result": hedge_result,
            "hedge_status": hedge_status
        }


MarketPortfolioPredictiveVarHedgeSynthesizer = PredictiveVarHedgeSynthesizer