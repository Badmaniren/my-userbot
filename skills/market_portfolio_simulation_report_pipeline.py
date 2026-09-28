import json
import logging
import os
import uuid
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline

logger = logging.getLogger("MarketPortfolioSimulationReportPipeline")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class SimulationReportPipelineError(Exception):
    """Кастомное исключение для ошибок пайплайна отчетов по симуляции портфеля."""
    pass


class MarketPortfolioSimulationReportPipeline:
    def __init__(self, storage_file: str = "portfolio_simulation.db"):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file=self.storage_file)
        self.execution_pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)

    def _ensure_symbol_data(self, symbol: str, default_price: float = 100.0, default_volume: float = 1000.0):
        if not symbol or not isinstance(symbol, str):
            return
        try:
            data = {}
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, "r") as f:
                        data = json.load(f)
                except (IOError, OSError, json.JSONDecodeError) as e:
                    logger.warning("Could not read JSON from %s: %s", self.storage_file, e)
                    data = {}
            if not isinstance(data, dict):
                data = {}
            if symbol not in data:
                data[symbol] = {
                    "symbol": symbol,
                    "price": default_price,
                    "current_price": default_price,
                    "quantity": default_volume
                }
                with open(self.storage_file, "w") as f:
                    json.dump(data, f)
        except (IOError, OSError) as e:
            logger.warning("Failed to persist default symbol data for %s: %s", symbol, e)

    def generate_simulation_report(
        self,
        symbol: str,
        percentage: float,
        slippage_factor: float,
        order_data: dict,
        market_context: dict
    ) -> dict:
        self._ensure_symbol_data(
            symbol=symbol,
            default_price=order_data.get("price", 100.0) if isinstance(order_data, dict) else 100.0,
            default_volume=order_data.get("volume", 1000.0) if isinstance(order_data, dict) else 1000.0
        )

        try:
            sim_result = self.simulator.simulate_scenario(
                symbol=symbol,
                percentage=percentage,
                slippage_factor=slippage_factor
            )
        except Exception as e:
            logger.error("Error running scenario simulation for %s: %s", symbol, e)
            raise SimulationReportPipelineError(str(e))

        try:
            exec_result = self.execution_pipeline.execute_order_simulation(
                order_data=order_data,
                market_context=market_context,
                percentage=percentage
            )
        except Exception as e:
            logger.error("Error executing order simulation for %s: %s", symbol, e)
            raise SimulationReportPipelineError(str(e))

        return {
            "report_id": uuid.uuid4().hex,
            "symbol": symbol,
            "scenario_simulation": sim_result,
            "execution_simulation": exec_result
        }

    def run_batch_report_pipeline(
        self,
        ticker: str,
        shifts: list,
        volume: int,
        scenario_name: str
    ) -> dict:
        self._ensure_symbol_data(
            symbol=ticker,
            default_price=100.0,
            default_volume=float(volume)
        )

        try:
            stress_sim = self.simulator.run_stress_test(
                symbol=ticker,
                shifts=shifts
            )
        except Exception as e:
            logger.error("Error running batch stress test for %s: %s", ticker, e)
            raise SimulationReportPipelineError(str(e))

        try:
            stress_exec = self.execution_pipeline.run_stress_pipeline(
                ticker=ticker,
                shifts=shifts,
                volume=volume,
                scenario_name=scenario_name
            )
        except Exception as e:
            logger.error("Error running stress pipeline execution for %s: %s", ticker, e)
            raise SimulationReportPipelineError(str(e))

        return {
            "batch_id": uuid.uuid4().hex,
            "ticker": ticker,
            "stress_simulation": stress_sim,
            "stress_execution": stress_exec
        }


def generate_portfolio_simulation_report(
    storage_file: str,
    order_data: dict,
    market_context: dict,
    percentage: float,
    shifts: list
) -> dict:
    pipeline = MarketPortfolioSimulationReportPipeline(storage_file=storage_file)
    symbol = order_data.get("symbol") or order_data.get("ticker") or "UNKNOWN"

    pipeline._ensure_symbol_data(
        symbol=symbol,
        default_price=order_data.get("price", 100.0) if isinstance(order_data, dict) else 100.0,
        default_volume=order_data.get("volume", 1000.0) if isinstance(order_data, dict) else 1000.0
    )

    try:
        scenario_result = pipeline.simulator.simulate_scenario(
            symbol=symbol,
            percentage=percentage,
            slippage_factor=0.01
        )
    except Exception as e:
        logger.warning("Scenario simulation fallback used for %s: %s", symbol, e)
        scenario_result = {
            "symbol": symbol,
            "simulated_price": order_data.get("price", 100.0) * (1 + percentage / 100.0),
            "pnl_impact": 0.0,
            "portfolio_value_delta": 0.0
        }

    execution_result = pipeline.execution_pipeline.execute_order_simulation(
        order_data=order_data,
        market_context=market_context,
        percentage=percentage
    )

    return {
        "report_id": uuid.uuid4().hex,
        "symbol": symbol,
        "scenario_simulation": scenario_result,
        "execution_pipeline": execution_result
    }
