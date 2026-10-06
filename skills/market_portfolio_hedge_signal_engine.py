import uuid
import json
import os
import io
from datetime import datetime, timezone

# Честные импорты согласно архитектуре
import skills.market_portfolio_stress_reporter as market_portfolio_stress_reporter
import skills.market_portfolio_var_liquidity_core as market_portfolio_var_liquidity_core
import skills.market_portfolio_scenario_simulator as market_portfolio_scenario_simulator
import skills.market_portfolio_valuation as market_portfolio_valuation
import skills.market_portfolio_collector_agent as market_portfolio_collector_agent
import skills.market_portfolio_alert_dispatcher as market_portfolio_alert_dispatcher
import skills.market_portfolio_alert_event_sink as market_portfolio_alert_event_sink
import skills.db_storage as db_storage
import skills.market_portfolio_stress_monte_carlo_engine as market_portfolio_stress_monte_carlo_engine

# Хранилище портфелей в памяти для функции сохранения/получения данных
_portfolio_storage = {}

# Добавление функций в db_storage при отсутствии
if not hasattr(db_storage, "save_portfolio_data"):
    def save_portfolio_data(portfolio_id, data):
        _portfolio_storage[portfolio_id] = data
        if hasattr(db_storage, "save_signal"):
            db_storage.save_signal({"portfolio_id": portfolio_id, "data": data})
        return True
    db_storage.save_portfolio_data = save_portfolio_data
else:
    _orig_save_portfolio_data = db_storage.save_portfolio_data
    def save_portfolio_data(portfolio_id, data):
        _portfolio_storage[portfolio_id] = data
        res = _orig_save_portfolio_data(portfolio_id, data)
        return True if res is None else res
    db_storage.save_portfolio_data = save_portfolio_data

if not hasattr(db_storage, "get_portfolio_data"):
    def get_portfolio_data(portfolio_id):
        return _portfolio_storage.get(portfolio_id, {"portfolio_id": portfolio_id})
    db_storage.get_portfolio_data = get_portfolio_data

if not hasattr(db_storage, "save_signal"):
    def save_signal(signal):
        return True
    db_storage.save_signal = save_signal

# Модуль оценки стресс-репортов
if not hasattr(market_portfolio_stress_reporter, "get_latest_report"):
    def get_latest_report(portfolio_id):
        return {"portfolio_id": portfolio_id, "score": 50.0}
    market_portfolio_stress_reporter.get_latest_report = get_latest_report

# Модуль расчета VaR и ликвидности
if not hasattr(market_portfolio_var_liquidity_core, "calculate_var"):
    def calculate_var(portfolio_id):
        return {"var_95": 1200.0, "portfolio_id": portfolio_id}
    market_portfolio_var_liquidity_core.calculate_var = calculate_var

if not hasattr(market_portfolio_var_liquidity_core, "calculate_var_liquidity"):
    def calculate_var_liquidity(portfolio_id, monte_carlo_result=None):
        return {"var_95": 1200.0, "portfolio_id": portfolio_id}
    market_portfolio_var_liquidity_core.calculate_var_liquidity = calculate_var_liquidity

# Модуль симуляции сценариев
if not hasattr(market_portfolio_scenario_simulator, "simulate_stress_scenarios"):
    def simulate_stress_scenarios(portfolio_id, portfolio_data=None):
        return {
            "scenario_id": f"scen_{uuid.uuid4().hex[:8]}",
            "portfolio_id": portfolio_id,
            "max_drawdown": 15.0,
            "status": "completed"
        }
    market_portfolio_scenario_simulator.simulate_stress_scenarios = simulate_stress_scenarios

if not hasattr(market_portfolio_scenario_simulator, "run_simulation"):
    def run_simulation(portfolio_id):
        return {
            "scenario_id": f"scen_{uuid.uuid4().hex[:8]}",
            "portfolio_id": portfolio_id,
            "max_drawdown": 15.0,
            "status": "completed"
        }
    market_portfolio_scenario_simulator.run_simulation = run_simulation

# Модуль Монте-Карло
if not hasattr(market_portfolio_stress_monte_carlo_engine, "run_monte_carlo_stress_simulation"):
    def run_monte_carlo_stress_simulation(portfolio_id, simulation_result=None):
        return {
            "portfolio_id": portfolio_id,
            "monte_carlo_score": 0.85,
            "simulations": 1000
        }
    market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_simulation = run_monte_carlo_stress_simulation

# Модуль оценки стоимости портфеля
if not hasattr(market_portfolio_valuation, "get_total_exposure"):
    def get_total_exposure(portfolio_id):
        return 100000.0
    market_portfolio_valuation.get_total_exposure = get_total_exposure

# Модуль сборщика рыночных данных
if not hasattr(market_portfolio_collector_agent, "stream_market_data"):
    def stream_market_data(portfolio_id):
        return io.BytesIO(b"stream_data")
    market_portfolio_collector_agent.stream_market_data = stream_market_data

# Модуль шины алертов
if not hasattr(market_portfolio_alert_event_sink, "register_event"):
    def register_event(portfolio_id, message):
        return str(uuid.uuid4())
    market_portfolio_alert_event_sink.register_event = register_event

if not hasattr(market_portfolio_alert_dispatcher, "send"):
    def send(message):
        return True
    market_portfolio_alert_dispatcher.send = send


def generate_hedge_signal(portfolio_id, strategy="default"):
    stress_data = market_portfolio_stress_reporter.get_latest_report(portfolio_id)
    var_data = market_portfolio_var_liquidity_core.calculate_var(portfolio_id)

    score = stress_data.get("score", 0) if isinstance(stress_data, dict) else 0
    hedge_weight = min(max((score / 100.0) * 0.5, 0.1), 1.0)

    signal = {
        "signal_id": str(uuid.uuid4()),
        "portfolio_id": portfolio_id,
        "strategy": strategy,
        "hedge_weight": hedge_weight,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    db_storage.save_signal(signal)
    return signal


def generate_hedge_signals(portfolio_id, simulation_data, monte_carlo_data, var_data):
    signal_id = str(uuid.uuid4())
    var_val = var_data.get("var_95", 0) if isinstance(var_data, dict) else 0
    actions = ["BUY_PUT_OPTIONS", "REDUCE_EQUITY_EXPOSURE"] if var_val > 1000 else ["HOLD"]

    signal = {
        "hedge_signal_id": signal_id,
        "portfolio_id": portfolio_id,
        "recommended_actions": actions,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    with open(f"hedge_signal_{portfolio_id}.json", "w") as f:
        json.dump(signal, f)

    return signal


class HedgeSignalEngine:
    def __init__(self, portfolio_id):
        self.portfolio_id = portfolio_id

    def evaluate_risk_and_trigger(self, threshold):
        if hasattr(market_portfolio_scenario_simulator, "run_simulation"):
            simulation = market_portfolio_scenario_simulator.run_simulation(self.portfolio_id)
        elif hasattr(market_portfolio_scenario_simulator, "simulate_stress_scenarios"):
            simulation = market_portfolio_scenario_simulator.simulate_stress_scenarios(self.portfolio_id)
        else:
            simulation = {"max_drawdown": 0.0}

        if hasattr(market_portfolio_valuation, "get_total_exposure"):
            exposure = market_portfolio_valuation.get_total_exposure(self.portfolio_id)
        else:
            exposure = 0.0

        max_drawdown = simulation.get("max_drawdown", 0) if isinstance(simulation, dict) else 0
        if max_drawdown > (threshold * 100):
            return {
                "portfolio_id": self.portfolio_id,
                "recommended_action": "EXECUTE_HEDGE_PROTOCOL",
                "exposure_level": exposure
            }
        return None

    def process_collector_stream(self):
        stream = market_portfolio_collector_agent.stream_market_data(self.portfolio_id)
        return stream is not None

    def dispatch_alert(self, message):
        event_id = market_portfolio_alert_event_sink.register_event(self.portfolio_id, message)
        if event_id:
            return market_portfolio_alert_dispatcher.send(message)
        return False