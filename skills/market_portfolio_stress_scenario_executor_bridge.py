from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator

class PortfolioStressScenarioExecutorBridge:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.pipeline = PortfolioStressScenarioPipeline(storage_file)
        self.simulator = PortfolioScenarioSimulator(storage_file)

    def execute_stress_workflow(self, symbol: str, percentage: float, shifts: list) -> dict:
        pipeline_report = self.pipeline.execute(symbol, percentage, shifts)
        simulation_res = self.simulator.run_stress_test(symbol, shifts)
        
        simulation_report = simulation_res if isinstance(simulation_res, dict) else {"results": simulation_res}
        
        return {
            "pipeline_report": pipeline_report,
            "simulation_report": simulation_report
        }

    def execute_stress_test_workflow(self, symbol: str, percentage: float, shifts: list) -> dict:
        pipeline_result = self.pipeline.execute(symbol, percentage, shifts)
        simulation_res = self.simulator.run_stress_test(symbol, shifts)
        
        simulation_result = simulation_res if isinstance(simulation_res, dict) else {"results": simulation_res}
        
        return {
            "pipeline_result": pipeline_result,
            "simulation_result": simulation_result
        }


def execute_stress_execution_bridge(storage_file: str, symbol: str, percentage: float, shifts: list) -> dict:
    bridge = PortfolioStressScenarioExecutorBridge(storage_file)
    return bridge.execute_stress_workflow(symbol, percentage, shifts)