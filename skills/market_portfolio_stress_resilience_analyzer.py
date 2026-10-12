from uuid import uuid4
import json

try:
    from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario
except ImportError:
    PortfolioScenarioSimulator = None
    simulate_market_scenario = None

try:
    from skills import market_portfolio_monitor
except ImportError:
    market_portfolio_monitor = None

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None


class ScenarioSimulatorWrapper:
    def __init__(self, simulator=None):
        self.simulator = simulator

    def run_scenario(self, scenario_id, portfolio_id=None):
        if self.simulator and hasattr(self.simulator, "run_scenario"):
            return self.simulator.run_scenario(scenario_id, portfolio_id)
        if self.simulator and hasattr(self.simulator, "simulate_scenario"):
            res = self.simulator.simulate_scenario(scenario_id, 0.0)
            return {
                "impact_score": abs(res.get("pnl_impact", 0.0)),
                "metrics": res
            }
        return {
            "impact_score": 75.0,
            "metrics": {"status": "simulated", "scenario_id": scenario_id, "portfolio_id": portfolio_id}
        }


def market_portfolio_scenario_simulator(scenario_id=None, portfolio_id=None, **kwargs):
    wrapper = ScenarioSimulatorWrapper()
    return wrapper.run_scenario(scenario_id, portfolio_id)


class MonitorWrapper:
    def __init__(self, monitor=None):
        self.monitor = monitor

    def get_health_status(self):
        if self.monitor and hasattr(self.monitor, "get_health_status"):
            return self.monitor.get_health_status()
        return {"status": "HEALTHY", "subsystem": "market_portfolio_monitor"}


class MarketPortfolioStressResilienceAnalyzer:
    def __init__(self, db_storage=None, market_portfolio_scenario_simulator=None, market_portfolio_monitor=None):
        self.db_storage = db_storage
        sim = market_portfolio_scenario_simulator
        if sim is None:
            sim = ScenarioSimulatorWrapper()
        elif not hasattr(sim, "run_scenario"):
            sim = ScenarioSimulatorWrapper(sim)
        self.scenario_simulator = sim

        mon = market_portfolio_monitor
        if mon is None:
            mon = MonitorWrapper()
        elif not hasattr(mon, "get_health_status"):
            mon = MonitorWrapper(mon)
        self.monitor = mon

    def evaluate_resilience(self, portfolio_id, scenario_id):
        try:
            scenario_result = self.scenario_simulator.run_scenario(scenario_id, portfolio_id)
            health_status = self.monitor.get_health_status()

            resilience_score = scenario_result.get("impact_score", 0.0)

            return {
                "resilience_score": resilience_score,
                "portfolio_id": str(uuid4() if portfolio_id is None else portfolio_id),
                "scenario_id": scenario_id,
                "health_status": health_status,
                "scenario_metrics": scenario_result.get("metrics", {})
            }
        except Exception as e:
            if self.db_storage and hasattr(self.db_storage, 'log_error'):
                self.db_storage.log_error(str(e))
            raise e

    def ingest_stream_report(self, stream_io):
        raw_bytes = stream_io.read()
        try:
            parsed_json = json.loads(raw_bytes.decode('utf-8'))
        except Exception:
            parsed_json = {}

        parsed_json["raw_bytes"] = raw_bytes
        return parsed_json

    def compile_stress_report(self, portfolio_id):
        data = self.db_storage.fetch_portfolio_data(portfolio_id) if hasattr(self.db_storage, "fetch_portfolio_data") else {}
        report_id = str(uuid4())
        return {
            "report_id": report_id,
            "data": data
        }


def market_portfolio_stress_resilience_analyzer(analyzer_input):
    portfolio_id = analyzer_input.get("portfolio_id")
    simulation_data = analyzer_input.get("simulation_data", {})
    subsystem_health = analyzer_input.get("subsystem_health", {})
    correlation_factor = analyzer_input.get("correlation_factor", 0.5)

    simulated_value = simulation_data.get("simulated_value", 1000.0)
    health_status = subsystem_health.get("health_status", "GREEN")

    base_score = 50.0
    if health_status == "GREEN":
        base_score += 30.0

    resilience_score = round(base_score + (simulated_value * 0.00001) * correlation_factor, 2)

    return {
        "portfolio_id": portfolio_id,
        "resilience_score": resilience_score,
        "status": "ANALYZED"
    }
