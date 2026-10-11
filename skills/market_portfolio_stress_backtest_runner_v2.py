import uuid
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine


class StressBacktestRunnerV2:
    def __init__(self, filepath=None, db_storage=None, extractor_tool=None, market_anomaly_detector=None, backtester=None, predictive_var_engine=None):
        self.filepath = filepath
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector

        if backtester is not None:
            self.backtester = backtester
        else:
            self.backtester = MarketPortfolioBacktester(filepath=self.filepath)

        if predictive_var_engine is not None:
            self.var_engine = predictive_var_engine
        else:
            self.var_engine = PredictiveVarEngine(
                db_storage=self.db_storage,
                extractor_tool=self.extractor_tool,
                market_anomaly_detector=self.market_anomaly_detector
            )

    def run_pipeline_simulation(
        self,
        symbol,
        portfolio_id,
        strategy_params,
        scenario_params,
        confidence_level,
        horizon_days,
        iterations,
        initial_capital=None
    ):
        if self.filepath and hasattr(self.backtester, "load_data"):
            self.backtester.load_data(self.filepath)

        # Retrieve initial capital safely from argument, backtester, or default to 100000.0
        if initial_capital is not None:
            capital = initial_capital
        else:
            capital = getattr(self.backtester, "initial_capital", 100000.0)

        equity_data = self.backtester.run_backtest(symbol, capital, strategy_params)
        summary = self.backtester.get_backtest_summary(symbol)

        # Retrieve portfolio value safely from summary if available, else fallback to capital
        portfolio_value = summary.get("final_equity", capital) if isinstance(summary, dict) else capital

        var_value = self.var_engine.calculate_predictive_stress_var(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

        simulation_id = uuid.uuid4().hex

        return {
            "symbol": symbol,
            "portfolio_id": portfolio_id,
            "backtest_summary": summary,
            "predictive_stress_var": var_value,
            "simulation_id": simulation_id
        }

    def execute_stream_stress_validation(self, stream_payload):
        return self.var_engine.process_market_stream(stream_payload)

    def run_stress_backtest_pipeline(
        self,
        portfolio_id,
        symbol,
        filepath,
        initial_capital,
        strategy_params,
        scenario_code,
        portfolio_value,
        scenario_params,
        confidence_level,
        horizon_days,
        iterations
    ):
        if filepath and hasattr(self.backtester, "load_data"):
            self.backtester.load_data(filepath)

        if hasattr(self.backtester, "initial_capital"):
            self.backtester.initial_capital = initial_capital

        equity_data = self.backtester.run_backtest(symbol, initial_capital, strategy_params)
        summary = self.backtester.get_backtest_summary(symbol)

        var_value = self.var_engine.calculate_predictive_stress_var(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations
        )

        return {
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "backtest_summary": summary,
            "predictive_var": var_value,
            "scenario_code": scenario_code,
            "portfolio_value": portfolio_value
        }