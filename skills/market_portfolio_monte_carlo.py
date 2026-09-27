import io
import json
import logging
import math
import pickle
import random
import uuid

from skills.db_storage import db_storage

mpmc_logger = logging.getLogger("market_portfolio_monte_carlo")
if not mpmc_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    mpmc_logger.addHandler(handler)
mpmc_logger.setLevel(logging.INFO)


class MonteCarloConfig:
    def __init__(
        self,
        num_simulations=100,
        time_horizon=30,
        confidence_level=0.95,
        random_seed=None,
        enable_slippage=False,
    ):
        self.num_simulations = num_simulations
        self.time_horizon = time_horizon
        self.confidence_level = confidence_level
        self.random_seed = random_seed
        self.enable_slippage = enable_slippage


class MonteCarloResult:
    def __init__(
        self,
        simulation_id,
        returns,
        mean_return,
        median_return,
        var,
        cvar,
        max_drawdown,
        percentiles,
        metrics=None,
    ):
        self.simulation_id = simulation_id
        self.returns = returns
        self.mean_return = mean_return
        self.median_return = median_return
        self.var = var
        self.cvar = cvar
        self.max_drawdown = max_drawdown
        self.percentiles = percentiles
        self.metrics = metrics or {}

    def to_dict(self):
        return {
            "simulation_id": self.simulation_id,
            "returns": self.returns,
            "mean_return": self.mean_return,
            "median_return": self.median_return,
            "var": self.var,
            "cvar": self.cvar,
            "max_drawdown": self.max_drawdown,
            "percentiles": self.percentiles,
            "metrics": self.metrics,
        }


class MarketPortfolioMonteCarlo:
    def __init__(self, scenario_simulator=None, slippage_model=None, config=None):
        self.scenario_simulator = scenario_simulator
        self.slippage_model = slippage_model
        self.config = config or MonteCarloConfig()

    def calculate_var(self, returns, confidence_level=0.95):
        if not returns or not (0.0 < confidence_level < 1.0):
            raise ValueError("Invalid returns or confidence level")
        sorted_returns = sorted(returns)
        index = int(math.floor((1.0 - confidence_level) * len(sorted_returns)))
        return sorted_returns[index]

    def calculate_cvar(self, returns, confidence_level=0.95):
        if not returns or not (0.0 < confidence_level < 1.0):
            raise ValueError("Invalid returns or confidence level")
        sorted_returns = sorted(returns)
        cutoff_index = int(math.floor((1.0 - confidence_level) * len(sorted_returns)))
        tail = sorted_returns[: cutoff_index + 1]
        return sum(tail) / len(tail) if tail else 0.0

    def calculate_drawdown(self, trajectory):
        if not trajectory:
            return 0.0
        max_dd = 0.0
        peak = trajectory[0]
        for val in trajectory:
            if val > peak:
                peak = val
            if peak > 0:
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd
        return max_dd

    def run_simulation(self, portfolio):
        if not portfolio.get("assets"):
            raise ValueError("Portfolio has no assets")
        if portfolio.get("total_value", 0) < 0:
            raise ValueError("Portfolio total value cannot be negative")

        weights_sum = sum(asset.get("weight", 0) for asset in portfolio["assets"])
        if not math.isclose(weights_sum, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise ValueError("Portfolio weights must sum to 1.0")

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        scenarios = []
        if self.scenario_simulator is not None:
            raw_scen = self.scenario_simulator.generate_scenarios()
            for sc in raw_scen:
                scenarios.append(sc)

        returns = []
        slippage_penalty = 0.0
        if self.config.enable_slippage and self.slippage_model is not None:
            slippage_penalty = self.slippage_model.estimate_slippage(portfolio)

        for i in range(self.config.num_simulations):
            if scenarios and i < len(scenarios):
                asset_rets = scenarios[i].get("asset_returns", {})
                sim_ret = sum(
                    asset_rets.get(asset["ticker"], asset.get("expected_return", 0.0))
                    * asset["weight"]
                    for asset in portfolio["assets"]
                )
            else:
                sim_ret = sum(
                    asset.get("expected_return", 0.0) * asset["weight"]
                    for asset in portfolio["assets"]
                )
                sim_ret += random.gauss(0, 0.05)

            if self.config.enable_slippage:
                sim_ret -= slippage_penalty

            returns.append(sim_ret)

        returns.sort()
        mean_ret = sum(returns) / len(returns) if returns else 0.0
        median_ret = returns[len(returns) // 2] if returns else 0.0
        var_val = self.calculate_var(returns, self.config.confidence_level)
        cvar_val = self.calculate_cvar(returns, self.config.confidence_level)

        trajectory = [portfolio["total_value"]]
        curr = portfolio["total_value"]
        for r in returns[: self.config.time_horizon]:
            curr *= 1.0 + r
            trajectory.append(curr)

        max_dd = self.calculate_drawdown(trajectory)

        percentiles = {
            "5%": self.calculate_var(returns, 0.95),
            "50%": median_ret,
            "95%": returns[int(0.95 * len(returns)) - 1] if returns else 0.0,
        }

        sim_id = f"sim_{uuid.uuid4().hex}"
        return MonteCarloResult(
            simulation_id=sim_id,
            returns=returns,
            mean_return=mean_ret,
            median_return=median_ret,
            var=var_val,
            cvar=cvar_val,
            max_drawdown=max_dd,
            percentiles=percentiles,
            metrics={"status": "completed"},
        )

    def run_stress_scenario(self, portfolio, market_shock=-0.2):
        mpmc_logger.info("Running stress scenario with shock factor %s", market_shock)
        stressed_returns = [market_shock + random.gauss(0, 0.02) for _ in range(50)]
        stressed_var = self.calculate_var(stressed_returns, self.config.confidence_level)
        stressed_cvar = self.calculate_cvar(stressed_returns, self.config.confidence_level)
        return {
            "shock_factor": market_shock,
            "stressed_var": stressed_var,
            "stressed_cvar": stressed_cvar,
            "portfolio_id": portfolio.get("portfolio_id"),
        }

    def export_results_json(self, result, stream):
        data = result.to_dict()
        stream.write(json.dumps(data))

    def export_binary_report(self, result, stream):
        header = b"MPMC_REPORT"
        payload = pickle.dumps(result.to_dict())
        stream.write(header + payload)


def market_portfolio_monte_carlo(monte_carlo_input):
    portfolio_id = monte_carlo_input.get("portfolio_id")
    iterations = monte_carlo_input.get("iterations", 100)
    scenarios_data = monte_carlo_input.get("scenarios", [])

    if isinstance(scenarios_data, dict):
        scenario_items = scenarios_data.get(
            "scenarios", scenarios_data.get("simulations", [])
        )
        if not scenario_items and "asset_returns" in scenarios_data:
            scenario_items = [scenarios_data]
    elif isinstance(scenarios_data, list):
        scenario_items = scenarios_data
    else:
        scenario_items = []

    returns = []
    for sc in scenario_items:
        if isinstance(sc, (int, float)):
            returns.append(float(sc))
        elif isinstance(sc, dict):
            if "portfolio_return" in sc:
                returns.append(float(sc["portfolio_return"]))
            elif "return" in sc:
                returns.append(float(sc["return"]))
            elif "asset_returns" in sc:
                asset_rets = sc.get("asset_returns", {})
                if isinstance(asset_rets, dict) and asset_rets:
                    avg_ret = sum(asset_rets.values()) / len(asset_rets)
                    returns.append(avg_ret)
                elif isinstance(asset_rets, list) and asset_rets:
                    returns.append(sum(asset_rets) / len(asset_rets))

    if not returns:
        returns = [random.gauss(0.01, 0.05) for _ in range(iterations)]

    returns.sort()
    mean_ret = sum(returns) / len(returns) if returns else 0.0
    var_95 = returns[int(0.05 * len(returns))] if returns else 0.0

    sim_id = f"sim_{uuid.uuid4().hex}"
    result_dict = {
        "simulation_id": sim_id,
        "portfolio_id": portfolio_id,
        "VaR_95": var_95,
        "expected_return": mean_ret,
        "returns": returns,
    }

    db_storage(
        "save",
        {
            "table": "monte_carlo_results",
            "id": sim_id,
            "data": result_dict,
            "portfolio_id": portfolio_id,
            **result_dict,
        },
    )

    return result_dict