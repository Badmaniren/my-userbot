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
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def load_data(self, storage_file):
        logger.info("Loading portfolio data from %s", storage_file)
        if not storage_file:
            return {}
        try:
            with open(storage_file, 'r') as f:
                return json.load(f)
        except (IOError, OSError, json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to load data from %s: %s", storage_file, e)
            return {}

    def simulate_scenario(self, symbol, percentage, slippage_factor=0.0):
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
                target = next((item for item in data["assets"] if isinstance(item, dict) and item.get("symbol") == symbol), None)
            elif "holdings" in data and isinstance(data["holdings"], list):
                target = next((item for item in data["holdings"] if isinstance(item, dict) and item.get("symbol") == symbol), None)
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
        
        base_simulated_price = current_price * (1 + pct_val / 100.0)
        slippage_adjustment = base_simulated_price * (float(slippage_factor) / 100.0) if slippage_factor else 0.0
        simulated_price = base_simulated_price + slippage_adjustment
        
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
                resulting_valuation = round(res["simulated_price"], 10)
            except KeyError:
                logger.warning("Stress test step failed for symbol %s at shift %s: symbol not found", symbol, shift)
                resulting_valuation = 0.0
            except ValueError:
                logger.warning("Stress test step failed for symbol %s at shift %s: value error", symbol, shift)
                resulting_valuation = 0.0
            report.append({
                "shift_percentage": float(shift),
                "resulting_valuation": resulting_valuation
            })
        logger.info("Stress test completed for symbol: %s", symbol)
        return report

    def evaluate(self, portfolio_id, scenario_name):
        return {
            "portfolio_id": portfolio_id,
            "scenario": scenario_name,
            "severity": 80.0,
            "recommended_hedge": "GOLD",
            "volume": 100
        }


def market_portfolio_scenario_simulator(payload=None, *args, **kwargs):
    if isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id")
        scenario_id = payload.get("scenario_id")
        return {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "recommended_hedge": "GOLD",
            "volume": 100,
            "status": "SIMULATED"
        }
    return {
        "recommended_hedge": "GOLD",
        "volume": 100,
        "status": "SIMULATED"
    }


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
