import json
import os
import logging

from skills.market_parser import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation

logger = logging.getLogger("PortfolioScenarioSimulator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class PortfolioScenarioSimulator:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def load_data(self, storage_file):
        try:
            logger.info("Loading portfolio data from %s", storage_file)
            with open(storage_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error("Failed to load portfolio data: %s", e)
            return {}

    def simulate_scenario(self, symbol, percentage):
        logger.info("Starting simulation for symbol: %s with percentage shift: %s", symbol, percentage)
        
        if not isinstance(symbol, str) or not symbol.strip():
            logger.error("Validation error: invalid symbol format")
            raise ValueError("Invalid symbol parameter")
            
        try:
            pct_val = float(percentage)
        except (TypeError, ValueError) as e:
            logger.error("Validation error: invalid percentage format: %s", e)
            raise ValueError("Invalid percentage parameter")

        data = self.load_data(self.storage_file)
        
        target = None
        if isinstance(data, dict):
            if symbol in data:
                target = data[symbol]
            elif "assets" in data and isinstance(data["assets"], list):
                target = next((item for item in data["assets"] if item.get("symbol") == symbol), None)
            elif "holdings" in data and isinstance(data["holdings"], list):
                target = next((item for item in data["holdings"] if item.get("symbol") == symbol), None)
            elif data.get("symbol") == symbol:
                target = data
        elif isinstance(data, list):
            target = next((item for item in data if isinstance(item, dict) and item.get("symbol") == symbol), None)
        
        if not target:
            logger.error("Symbol %s not found in portfolio data", symbol)
            raise KeyError(f"Symbol {symbol} not found")

        current_price = target.get("current_price") or target.get("price") or 0.0
        quantity = target.get("quantity") or target.get("shares") or 0.0
        
        logger.info("Found target for %s: price=%.4f, quantity=%.4f", symbol, current_price, quantity)
        
        simulated_price = current_price * (1 + pct_val / 100.0)
        pnl_impact = (simulated_price - current_price) * quantity
        
        logger.info("Simulation completed for %s: simulated_price=%.4f, pnl_impact=%.4f", symbol, simulated_price, pnl_impact)
        
        return {
            "symbol": symbol,
            "simulated_price": simulated_price,
            "pnl_impact": pnl_impact,
            "portfolio_value_delta": pnl_impact
        }

    def run_stress_test(self, symbol, shifts):
        logger.info("Running stress test for symbol: %s with shifts: %s", symbol, shifts)
        report = []
        for shift in shifts:
            try:
                res = self.simulate_scenario(symbol, shift)
                resulting_valuation = res["simulated_price"]
            except KeyError:
                logger.warning("Stress test step failed for symbol %s at shift %s: symbol not found", symbol, shift)
                resulting_valuation = 0.0
            except ValueError:
                logger.warning("Stress test step failed for symbol %s at shift %s: value error", symbol, shift)
                resulting_valuation = 0.0
            report.append({
                "shift_percentage": shift,
                "resulting_valuation": resulting_valuation
            })
        logger.info("Stress test completed for symbol: %s", symbol)
        return report

def simulate_market_scenario(storage_file, symbol, percentage):
    logger.info("Wrapper simulate_market_scenario invoked for %s", symbol)
    simulator = PortfolioScenarioSimulator(storage_file)
    return simulator.simulate_scenario(symbol, percentage)

def run_stress_test(storage_file, symbol, range_min, range_max, step):
    logger.info("Wrapper run_stress_test invoked for %s range [%s, %s] step %s", symbol, range_min, range_max, step)
    simulator = PortfolioScenarioSimulator(storage_file)
    shifts = [float(x) for x in range(int(range_min), int(range_max) + 1, step)]
    scenarios = simulator.run_stress_test(symbol, shifts)
    return {
        "symbol": symbol,
        "scenarios": scenarios
    }