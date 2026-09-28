import logging
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel

logger = logging.getLogger("MarketPortfolioExecutionPipeline")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ExecutionPipelineError(Exception):
    """Исключение для ошибок в пайплайне исполнения."""
    pass


class MarketPortfolioExecutionPipeline:
    def __init__(self, storage_file: str = None):
        self.storage_file = storage_file
        self.slippage_model = MarketPortfolioSlippageModel()
        self.scenario_simulator = PortfolioScenarioSimulator(storage_file=storage_file)

    def _persist_logs_safely(self, simulation_id: str, executions: list):
        if hasattr(self.slippage_model, "persist_execution_logs"):
            try:
                self.slippage_model.persist_execution_logs(simulation_id, executions, self.storage_file)
            except TypeError:
                try:
                    self.slippage_model.persist_execution_logs(self.storage_file)
                except Exception as e:
                    logger.warning("Failed to persist execution logs: %s", e)
            except Exception as e:
                logger.warning("Failed to persist execution logs: %s", e)

    def execute_order_simulation(self, order_data: dict, market_context: dict, percentage: float) -> dict:
        try:
            ticker = order_data.get("ticker") or order_data.get("symbol")
            scenario_result = self.scenario_simulator.simulate_scenario(ticker, percentage)
            
            execution_result = self.slippage_model.simulate_order_execution(order_data, market_context)
            self._persist_logs_safely(ticker or "sim_id", [execution_result])

            return {
                "scenario_result": scenario_result,
                "execution_result": execution_result
            }
        except Exception as e:
            if isinstance(e, ExecutionPipelineError):
                raise e
            raise ExecutionPipelineError(f"Error in execute_order_simulation: {e}")

    def run_batch_pipeline_execution(self, orders: list, contexts: list, percentage: float) -> list:
        try:
            batch_results = self.slippage_model.simulate_batch(orders, contexts)
            self._persist_logs_safely("batch_id", batch_results)
            return batch_results
        except Exception as e:
            raise ExecutionPipelineError(f"Error in run_batch_pipeline_execution: {e}")

    def run_stress_pipeline(self, ticker: str, shifts: list, volume: float, scenario_name: str) -> dict:
        try:
            stress_scenario_res = self.scenario_simulator.run_stress_test(ticker, shifts)
            stress_slippage_res = self.slippage_model.simulate_stress_slippage(ticker, volume, scenario_name)

            return {
                "stress_scenario": stress_scenario_res,
                "stress_slippage": stress_slippage_res
            }
        except Exception as e:
            raise ExecutionPipelineError(f"Error in run_stress_pipeline: {e}")

    def get_historical_pipeline_logs(self, simulation_id: str) -> list:
        try:
            return self.slippage_model.get_execution_logs(simulation_id, self.storage_file)
        except Exception as e:
            logger.warning("Error fetching historical pipeline logs for %s: %s", simulation_id, e)
            return []

    def simulate_execution(self, symbol: str, volume: float, price: float, order_type: str, percentage_shift: float) -> dict:
        try:
            order_data = {"ticker": symbol, "symbol": symbol, "volume": volume, "price": price, "order_type": order_type}
            market_context = {"price": price}
            
            scenario_res = self.scenario_simulator.simulate_scenario(symbol, percentage_shift)
            
            if hasattr(self.slippage_model, "simulate_execution"):
                slip_res = self.slippage_model.simulate_execution(symbol, volume, price, order_type, percentage_shift)
            else:
                slip_res = self.slippage_model.simulate_order_execution(order_data, market_context)

            sim_id = slip_res.get("order_id") or slip_res.get("simulation_id") or "sim_id_123"
            slippage_val = slip_res.get("slippage", 0.0)
            executed_price = slip_res.get("executed_price", price + slippage_val if order_type == "BUY" else price - slippage_val)

            return {
                "simulation_id": sim_id,
                "symbol": symbol,
                "slippage": slippage_val,
                "scenario_result": scenario_res,
                "executed_price": executed_price
            }
        except Exception as e:
            raise ExecutionPipelineError(f"Error in simulate_execution: {e}")

    def run_stress_execution(self, symbol: str, volume: float, shifts: list) -> dict:
        try:
            stress_evaluations = []
            for shift in shifts:
                scenario_outcome = self.scenario_simulator.simulate_scenario(symbol, shift)
                if hasattr(self.slippage_model, "simulate_shift_slippage"):
                    slip_val = self.slippage_model.simulate_shift_slippage(symbol, volume, shift)
                else:
                    slip_val = 0.5 * abs(shift)
                
                stress_evaluations.append({
                    "shift_percentage": shift,
                    "slippage": slip_val,
                    "scenario_outcome": scenario_outcome
                })

            return {
                "symbol": symbol,
                "stress_evaluations": stress_evaluations
            }
        except Exception as e:
            raise ExecutionPipelineError(f"Error in run_stress_execution: {e}")
