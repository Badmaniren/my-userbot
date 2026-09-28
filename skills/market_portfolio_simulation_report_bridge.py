import os
import json
import logging
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, simulate_market_scenario
from skills.market_report_generator import MarketReportGenerator, generate_market_report

logger = logging.getLogger("PortfolioSimulationReportBridge")

class PortfolioSimulationReportBridge:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.generator = MarketReportGenerator(storage_file)

    def _ensure_symbol_data(self, symbol):
        if not symbol or not self.storage_file:
            return

        data = {}
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (IOError, OSError, json.JSONDecodeError) as e:
                logger.warning("Unable to read storage file %s when ensuring symbol data: %s", self.storage_file, e)
                data = {}

        symbol_exists = False
        if isinstance(data, dict):
            if symbol in data:
                symbol_exists = True
            elif "assets" in data and isinstance(data["assets"], list):
                symbol_exists = any(isinstance(item, dict) and item.get("symbol") == symbol for item in data["assets"])
            elif "holdings" in data and isinstance(data["holdings"], list):
                symbol_exists = any(isinstance(item, dict) and item.get("symbol") == symbol for item in data["holdings"])
            elif data.get("symbol") == symbol:
                symbol_exists = True
        elif isinstance(data, list):
            symbol_exists = any(isinstance(item, dict) and item.get("symbol") == symbol for item in data)

        if not symbol_exists:
            if not isinstance(data, dict):
                data = {}
            data[symbol] = {
                "symbol": symbol,
                "price": 100.0,
                "current_price": 100.0,
                "quantity": 10.0
            }
            try:
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except (IOError, OSError) as e:
                logger.warning("Unable to write storage file %s when ensuring symbol data: %s", self.storage_file, e)

    def simulate_and_report(self, symbol, percentage, slippage=None):
        self._ensure_symbol_data(symbol)
        if slippage is not None:
            sim_result = self.simulator.simulate_scenario(symbol, percentage, slippage)
        else:
            sim_result = self.simulator.simulate_scenario(symbol, percentage)

        rep_result = self.generator.generate_symbol_report(symbol)
        return {
            "simulation_data": sim_result,
            "report_data": rep_result
        }

    def execute_stress_test_workflow(self, symbol, shifts):
        self._ensure_symbol_data(symbol)
        stress_result = self.simulator.run_stress_test(symbol, shifts)
        stream_dump = self.generator.get_raw_stream_dump()
        return {
            "stress_data": stress_result,
            "stream_dump": stream_dump
        }

    def process_simulation_and_report(self, symbol, percentage):
        self._ensure_symbol_data(symbol)
        sim_result = self.simulator.simulate_scenario(symbol, percentage)
        rep_result = self.generator.generate_symbol_report(symbol)
        return {
            "simulation_result": sim_result,
            "report_data": rep_result,
            "symbol": symbol
        }

def generate_simulation_report(storage_file, symbol, percentage):
    bridge = PortfolioSimulationReportBridge(storage_file)
    bridge._ensure_symbol_data(symbol)
    sim_res = simulate_market_scenario(storage_file, symbol, percentage)
    rep_res = generate_market_report(storage_file, symbol)
    return {
        "simulation": sim_res,
        "report": rep_res
    }

def run_simulation_and_generate_report(storage_file, symbol, percentage):
    bridge = PortfolioSimulationReportBridge(storage_file)
    return bridge.process_simulation_and_report(symbol, percentage)
