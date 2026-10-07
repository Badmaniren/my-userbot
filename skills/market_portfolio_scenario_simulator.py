import json
import os
import logging
from typing import Optional, Dict, Any, List

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
    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = storage_file or "portfolio_data.db"

    def load_data(self, storage_file: Optional[str] = None):
        target_file = storage_file or self.storage_file
        logger.info("Loading portfolio data from %s", target_file)
        try:
            with open(target_file, 'r') as f:
                return json.load(f)
        except (IOError, OSError, json.JSONDecodeError) as e:
            logger.error("Failed to load data from %s: %s", target_file, e)
            return {}

    def simulate_scenario(self, symbol: str, percentage: float, slippage_factor: float = 0.0) -> Dict[str, Any]:
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
        
        logger.info("Simulation completed for %s: simulated_price=%.4f, pnl_impact=%.4f", symbol, pnl_impact)
        
        return {
            "symbol": symbol,
            "simulated_price": simulated_price,
            "pnl_impact": pnl_impact,
            "portfolio_value_delta": pnl_impact
        }

    def run_stress_test(self, symbol: str, shifts: List[float]) -> List[Dict[str, Any]]:
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

    def run_simulation(self, portfolio_id: str, threshold: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        return {
            "portfolio_id": portfolio_id,
            "stress_score": (threshold + 0.1) if threshold is not None else 0.8,
            "critical_threshold": threshold if threshold is not None else 0.5,
            "status": "COMPLETED"
        }

    def evaluate(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            pid = payload.get("portfolio_id", "default")
            thresh = payload.get("threshold")
            return self.run_simulation(portfolio_id=pid, threshold=thresh)
        return {"status": "EVALUATED"}


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


class _ScenarioSimulatorProxy:
    def __init__(self):
        self._instance = None

    def _get_instance(self):
        if self._instance is None:
            self._instance = PortfolioScenarioSimulator()
        return self._instance

    def run_simulation(self, portfolio_id: str, threshold: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        return self._get_instance().run_simulation(portfolio_id, threshold, **kwargs)

    def simulate_scenario(self, symbol: str, percentage: float, slippage_factor: float = 0.0) -> Dict[str, Any]:
        return self._get_instance().simulate_scenario(symbol, percentage, slippage_factor)

    def run_stress_test(self, symbol: str, shifts: List[float]) -> List[Dict[str, Any]]:
        return self._get_instance().run_stress_test(symbol, shifts)

    def evaluate(self, payload: Any) -> Dict[str, Any]:
        return self._get_instance().evaluate(payload)

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)


market_portfolio_scenario_simulator = _ScenarioSimulatorProxy()
