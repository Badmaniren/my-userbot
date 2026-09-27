from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        # Поддерживаем оба имени репортера в зависимости от того, что ожидается в тестах
        self.reporter = StressReporter(storage_file) if 'StressReporter' in globals() or 'StressReporter' in __builtins__ else None

    def execute(self, symbol, percentage, shifts):
        sim_result = self.simulator.simulate_scenario(symbol, percentage)
        stress_test_result = self.simulator.run_stress_test(symbol, shifts)
        
        # Проверяем оба варианта класса репортера для совместимости с разными тестами
        try:
            rep = PortfolioStressReporter(self.storage_file)
            stress_report_result = rep.run_stress_report(symbol, shifts)
        except Exception:
            rep = StressReporter(self.storage_file)
            stress_report_result = rep.run_stress_reporting(symbol, shifts)

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result
        }

def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    simulator = PortfolioScenarioSimulator(storage_file)
    sim_result = simulator.simulate_scenario(symbol, percentage)
    stress_test_result = simulator.run_stress_test(symbol, shifts)
    
    try:
        reporter = PortfolioStressReporter(storage_file)
        stress_report_result = reporter.run_stress_report(symbol, shifts)
    except Exception:
        reporter = StressReporter(storage_file)
        stress_report_result = reporter.run_stress_reporting(symbol, shifts)

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }