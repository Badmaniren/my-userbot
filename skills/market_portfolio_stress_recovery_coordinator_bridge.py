import os
import logging
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)
from skills.market_portfolio_monitor import start_new, run_pipeline

logger = logging.getLogger("StressRecoveryCoordinatorBridge")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class StressRecoveryCoordinatorBridge:
    def __init__(self, storage_file: str = "stress_recovery.db"):
        self.storage_file = storage_file
        logger.info(f"Initializing StressRecoveryCoordinatorBridge with storage: {storage_file}")
        
        if not os.path.exists(self.storage_file):
            logger.debug(f"Storage file {self.storage_file} does not exist. Creating default empty structure.")
            with open(self.storage_file, "w") as f:
                f.write("{}")

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
        logger.info(f"Executing recovery workflow for symbol: {symbol}, percentage: {percentage}, shifts: {shifts}")
        if not os.path.exists(self.storage_file):
            logger.debug(f"Storage file {self.storage_file} does not exist. Creating default empty structure.")
            with open(self.storage_file, "w") as f:
                f.write("{}")

        try:
            stress_result = self.pipeline.execute(symbol, percentage, shifts)
            logger.info(f"Stress scenario pipeline executed successfully for {symbol}")
        except KeyError as e:
            logger.warning(f"KeyError encountered during stress pipeline execution for {symbol}: {e}. Falling back to simulation.")
            stress_result = {"status": "simulated", "symbol": symbol, "percentage": percentage}

        recovery_result = run_pipeline(symbol, url, telegram_token, chat_id, self.storage_file)
        logger.info(f"Recovery pipeline finished for symbol: {symbol}")

        recovery_result = {"status": "success", "result": recovery_result}

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
    logger.info(f"Running stress recovery coordinator for {symbol} using storage {storage_file}")
    if not os.path.exists(storage_file):
        logger.debug(f"Storage file {storage_file} not found. Initializing.")
        with open(storage_file, "w") as f:
            f.write("{}")

    try:
        stress_output = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)
        logger.info(f"Stress scenario run successfully for {symbol}")
        monitor_output = start_new(symbol, url, telegram_token, chat_id, storage_file)
        monitor_output = {"status": "success", "result": monitor_output}
    except (KeyError, TypeError) as e:
        logger.warning(f"Caught exception {type(e).__name__} during stress scenario execution for {symbol}: {e}. Falling back.")
        stress_output = {"status": "simulated", "symbol": symbol, "shifts": shifts}
        monitor_output = start_new(symbol, url, telegram_token, chat_id, storage_file)
        if not isinstance(monitor_output, dict):
            monitor_output = {"status": "success", "result": monitor_output}

    logger.info(f"Monitor monitor_output started successfully for {symbol}")

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
    logger.info(f"Running stress recovery coordinator pipeline for {symbol} at price {price}")

    if not os.path.exists(storage_file):
        logger.debug(f"Storage file {storage_file} not found in pipeline. Initializing.")
        with open(storage_file, "w") as f:
            f.write("{}")

    coordinator = StressRecoveryCoordinatorBridge(storage_file=storage_file)

    shifts_iterable = list(range(shifts)) if isinstance(shifts, int) else shifts

    try:
        stress_result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts_iterable)
        logger.info(f"Stress scenario pipeline function executed successfully for {symbol}")
    except (KeyError, TypeError) as e:
        logger.warning(f"Caught exception {type(e).__name__} in pipeline for {symbol}: {e}. Providing fallback.")
        stress_result = {"status": "simulated", "symbol": symbol, "shifts": shifts_iterable}

    recovery_result = start_new(symbol, url, telegram_token, chat_id, storage_file)
    logger.info(f"Monitor start_new completed for pipeline execution on {symbol}")

    if not isinstance(recovery_result, dict):
        recovery_result = {"status": "success", "result": recovery_result}

    return {
        "stress": stress_result,
        "recovery": recovery_result
    }