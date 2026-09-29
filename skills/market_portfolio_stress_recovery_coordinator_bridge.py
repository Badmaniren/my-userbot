import os
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)
from skills.market_portfolio_monitor import start_new, run_pipeline

class StressRecoveryCoordinatorBridge:
    def __init__(self, storage_file: str = "stress_recovery.db"):
        self.storage_file = storage_file
        self.pipeline = PortfolioStressScenarioPipeline(storage_file)
        self.monitor = {"status": "initialized", "storage": storage_file}

    def execute_recovery_workflow(
        self,
        symbol: str,
        url: str,
        telegram_token: str,
        chat_id: str,
        percentage: float,
        shifts: int
    ) -> dict:
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, "w") as f:
                f.write("{}")
        
        try:
            stress_result = self.pipeline.execute(symbol, percentage, shifts)
        except KeyError:
            stress_result = {"status": "simulated", "symbol": symbol, "percentage": percentage}

        recovery_result = run_pipeline(symbol, url, telegram_token, chat_id, self.storage_file)
        return {
            "stress_result": stress_result,
            "recovery_result": recovery_result
        }

def run_stress_recovery_coordinator(
    storage_file: str,
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    percentage: float,
    shifts: int
) -> dict:
    if not os.path.exists(storage_file):
        with open(storage_file, "w") as f:
            f.write("{}")

    try:
        stress_output = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)
    except (KeyError, TypeError):
        stress_output = {"status": "simulated", "symbol": symbol, "shifts": shifts}

    monitor_output = start_new(symbol, url, telegram_token, chat_id, storage_file)
    return {
        "stress": stress_output,
        "recovery": monitor_output
    }

def run_stress_recovery_coordinator_pipeline(
    storage_file: str,
    symbol: str,
    price: float,
    percentage: float,
    shifts: int,
    telegram_token: str,
    chat_id: str,
    url: str
) -> dict:
    coordinator = StressRecoveryCoordinatorBridge(storage_file=storage_file)
    
    shifts_iterable = list(range(shifts)) if isinstance(shifts, int) else shifts
    
    if not os.path.exists(storage_file):
        with open(storage_file, "w") as f:
            f.write("{}")

    try:
        stress_result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts_iterable)
    except (KeyError, TypeError):
        stress_result = {"status": "simulated", "symbol": symbol, "shifts": list(range(shifts)) if isinstance(shifts, int) else shifts}

    recovery_result = start_new(symbol, url, telegram_token, chat_id, storage_file)
    
    return {
        "stress": stress_result,
        "recovery": recovery_result
    }