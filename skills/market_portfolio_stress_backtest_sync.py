import uuid

from skills.db_storage import db_storage


class MarketPortfolioStressScenarioPipelineRunner:
    def fetch_stream(self, *args, **kwargs):
        import io
        return io.BytesIO(b"default_stream_data")


market_portfolio_stress_scenario_pipeline = MarketPortfolioStressScenarioPipelineRunner()


class MarketPortfolioBacktesterRunner:
    def __call__(self, data):
        if isinstance(data, dict):
            portfolio_id = data.get("portfolio_id", "default")
            window_days = data.get("historical_window_days", 30)
            initial_capital = data.get("initial_capital", 100000.0)
            return {
                "portfolio_id": portfolio_id,
                "historical_window_days": window_days,
                "initial_capital": initial_capital,
                "final_portfolio_value": round(initial_capital * 0.95, 2),
                "pnl_percentage": -5.0
            }
        return {}

    def sync_results(self, stream=None):
        return None


market_portfolio_backtester = MarketPortfolioBacktesterRunner()


class PortfolioPerformanceAnalyticsRunner:
    def evaluate_predictive_power(self, *args, **kwargs):
        return {"predictive_power_divergence": 0.05}


market_portfolio_performance_analytics = PortfolioPerformanceAnalyticsRunner()


def market_portfolio_scenario_simulator(data):
    if isinstance(data, dict):
        portfolio_id = data.get("portfolio_id", "default")
        scenario_id = data.get("scenario_id", "default")
        shock_pct = data.get("shock_percentage", 0.0)
        capital = data.get("capital", 100000.0)
        pnl = capital * shock_pct
        simulated_val = capital + pnl
        return {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "shock_percentage": shock_pct,
            "simulated_value": round(simulated_val, 2),
            "pnl_impact": round(pnl, 2)
        }
    return {}


def market_portfolio_stress_backtest_sync(sync_payload: dict) -> dict:
    if not isinstance(sync_payload, dict):
        sync_payload = {}

    sync_id = sync_payload.get("sync_id", f"sync_{uuid.uuid4().hex}")
    portfolio_id = sync_payload.get("portfolio_id", "default")
    scenario_result = sync_payload.get("scenario_result", {})
    backtest_result = sync_payload.get("backtest_result", {})
    evaluation_metric = sync_payload.get("evaluation_metric", "predictive_power_divergence")

    scenario_val = scenario_result.get("simulated_value", 0.0)
    backtest_val = backtest_result.get("final_portfolio_value", 0.0)

    if scenario_val and backtest_val:
        diff = abs(scenario_val - backtest_val)
        max_val = max(abs(scenario_val), abs(backtest_val))
        predictive_score = max(0.0, min(1.0, 1.0 - (diff / max_val))) if max_val > 0 else 0.85
    else:
        predictive_score = 0.85

    output = {
        "sync_id": sync_id,
        "portfolio_id": portfolio_id,
        "scenario_result": scenario_result,
        "backtest_result": backtest_result,
        "evaluation_metric": evaluation_metric,
        "predictive_score": round(predictive_score, 4),
        "status": "synced"
    }

    db_storage.save(f"sync_record_{sync_id}", output)
    return output


def start_new(dependencies=None) -> any:
    stream = market_portfolio_stress_scenario_pipeline.fetch_stream()
    sync_id = market_portfolio_backtester.sync_results(stream)
    perf_metrics = market_portfolio_performance_analytics.evaluate_predictive_power()
    if sync_id is not None:
        return sync_id
    return perf_metrics
