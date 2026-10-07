import uuid
from datetime import datetime

try:
    from skills.db_storage import db_storage
except ImportError:
    try:
        from skills import db_storage
    except ImportError:
        db_storage = None

import skills.market_portfolio_backtester as market_portfolio_backtester_mod
market_portfolio_backtester = getattr(market_portfolio_backtester_mod, "market_portfolio_backtester", getattr(market_portfolio_backtester_mod, "MarketPortfolioBacktester", None))

import skills.market_portfolio_stress_monte_carlo_engine as market_portfolio_stress_monte_carlo_engine_mod
market_portfolio_stress_monte_carlo_engine = getattr(market_portfolio_stress_monte_carlo_engine_mod, "market_portfolio_stress_monte_carlo_engine", getattr(market_portfolio_stress_monte_carlo_engine_mod, "MonteCarloStressEngine", None))

from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator


class MarketPortfolioStressBacktestCalibrator:
    def __init__(self, db_storage=None, market_portfolio_stress_monte_carlo_engine=None, market_portfolio_scenario_simulator=None):
        self.db_storage = db_storage if db_storage is not None else db_storage
        self.monte_carlo_engine = market_portfolio_stress_monte_carlo_engine if market_portfolio_stress_monte_carlo_engine is not None else market_portfolio_stress_monte_carlo_engine
        self.scenario_simulator = market_portfolio_scenario_simulator if market_portfolio_scenario_simulator is not None else market_portfolio_scenario_simulator

    def calibrate_backtest(self, portfolio_id: str, lookback_days: int, iterations: int):
        historical_stream = self.db_storage.fetch_historical_data(portfolio_id, lookback_days)
        content = historical_stream.read()
        if not content:
            raise ValueError("Insufficient historical data for calibration.")

        mc_results = self.monte_carlo_engine.run_simulations(portfolio_id, lookback_days, iterations)

        calibration_id = str(uuid.uuid4())
        return {
            "calibration_id": calibration_id,
            "portfolio_id": portfolio_id,
            "timestamp": datetime.now().timestamp(),
            "iterations": iterations,
            "metrics": {
                "var": mc_results.get("var"),
                "cvar": mc_results.get("cvar"),
            },
            "simulations": mc_results.get("simulations", iterations)
        }

    def recalibrate_scenario_matrix(self, scenario_id: str, confidence_level: float):
        result = self.scenario_simulator.evaluate_matrix(scenario_id, confidence_level)
        return result


def market_portfolio_stress_backtest_calibrator(
    portfolio_id: str,
    valuation: dict,
    backtest: dict,
    monte_carlo: dict,
    target_confidence: float
):
    calibration_id = str(uuid.uuid4())
    return {
        "calibration_id": calibration_id,
        "portfolio_id": portfolio_id,
        "target_confidence": target_confidence,
        "valuation": valuation,
        "backtest": backtest,
        "monte_carlo": monte_carlo,
        "status": "calibrated"
    }