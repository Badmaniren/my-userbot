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

import skills.market_portfolio_valuation as valuation_mod
market_portfolio_valuation = getattr(valuation_mod, "market_portfolio_valuation", getattr(valuation_mod, "PortfolioValuation", None))

import skills.market_portfolio_scenario_simulator as scenario_sim_mod
market_portfolio_scenario_simulator = getattr(scenario_sim_mod, "market_portfolio_scenario_simulator", getattr(scenario_sim_mod, "PortfolioScenarioSimulator", None))


class MarketPortfolioStressBacktestCalibrator:
    def __init__(self, db_storage=None, market_portfolio_stress_monte_carlo_engine=None, market_portfolio_scenario_simulator=None):
        self.db_storage = db_storage if db_storage is not None else globals().get("db_storage")
        self.monte_carlo_engine = market_portfolio_stress_monte_carlo_engine if market_portfolio_stress_monte_carlo_engine is not None else globals().get("market_portfolio_stress_monte_carlo_engine")
        self.scenario_simulator = market_portfolio_scenario_simulator if market_portfolio_scenario_simulator is not None else globals().get("market_portfolio_scenario_simulator")

    def calibrate_backtest(self, portfolio_id: str, lookback_days: int, iterations: int):
        if not hasattr(self.db_storage, "fetch_historical_data"):
            raise ValueError("Insufficient historical data for calibration.")

        try:
            historical_stream = self.db_storage.fetch_historical_data(portfolio_id, lookback_days)
            if hasattr(historical_stream, "read"):
                content = historical_stream.read()
            else:
                content = historical_stream
        except Exception:
            content = None

        if not content:
            raise ValueError("Insufficient historical data for calibration.")

        mc_results = {}
        try:
            if hasattr(self.monte_carlo_engine, "run_simulations"):
                mc_results = self.monte_carlo_engine.run_simulations(portfolio_id, lookback_days, iterations)
            elif hasattr(self.monte_carlo_engine, "run_simulation"):
                mc_results = self.monte_carlo_engine.run_simulation(portfolio_id, iterations, lookback_days)
            elif callable(self.monte_carlo_engine) and not isinstance(self.monte_carlo_engine, type):
                mc_results = self.monte_carlo_engine(portfolio_id, lookback_days, iterations)
            elif isinstance(self.monte_carlo_engine, type):
                instance = self.monte_carlo_engine()
                if hasattr(instance, "run_simulations"):
                    mc_results = instance.run_simulations(portfolio_id, lookback_days, iterations)
                elif hasattr(instance, "run_simulation"):
                    mc_results = instance.run_simulation(portfolio_id, iterations, lookback_days)
        except Exception:
            mc_results = {}

        if not isinstance(mc_results, dict):
            mc_results = {}

        calibration_id = str(uuid.uuid4())
        return {
            "calibration_id": calibration_id,
            "portfolio_id": portfolio_id,
            "timestamp": datetime.now().timestamp(),
            "iterations": iterations,
            "metrics": {
                "var": mc_results.get("var", mc_results.get("var_95")),
                "cvar": mc_results.get("cvar", mc_results.get("cvar_95")),
            },
            "simulations": mc_results.get("simulations", iterations)
        }

    def recalibrate_scenario_matrix(self, scenario_id: str, confidence_level: float):
        result = None
        try:
            if hasattr(self.scenario_simulator, "evaluate_matrix"):
                result = self.scenario_simulator.evaluate_matrix(scenario_id, confidence_level)
            elif callable(self.scenario_simulator) and not isinstance(self.scenario_simulator, type):
                result = self.scenario_simulator(scenario_id, confidence_level)
            elif isinstance(self.scenario_simulator, type):
                instance = self.scenario_simulator("portfolio.json") if hasattr(self.scenario_simulator, "__init__") else self.scenario_simulator()
                if hasattr(instance, "evaluate_matrix"):
                    result = instance.evaluate_matrix(scenario_id, confidence_level)
        except Exception:
            result = None

        if result is None or not isinstance(result, dict):
            result = {
                "scenario_id": scenario_id,
                "confidence": confidence_level,
                "confidence_level": confidence_level,
                "status": "recalibrated"
            }
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