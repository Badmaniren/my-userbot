import io
from skills import market_portfolio_monitor
from skills import market_portfolio_stress_reporter

def run_stress_recovery_pipeline(symbol, url, telegram_token, chat_id, storage_file, threshold=None):
    market_portfolio_monitor.run_pipeline(symbol, url, telegram_token, chat_id, storage_file)
    shifts = [threshold] if threshold is not None else [0.0]
    market_portfolio_stress_reporter.run_stress_reporting_pipeline(storage_file, symbol, shifts)
    return {"status": "success", "symbol": symbol}

def evaluate_and_recover(symbol, storage_file, drop_limit):
    market_portfolio_monitor.load_data(storage_file)
    reporter = market_portfolio_stress_reporter.StressReporter(storage_file)
    market_portfolio_stress_reporter.generate_stress_report(storage_file, symbol, drop_limit)
    market_portfolio_monitor.export_audit_logs(storage_file)
    return {"status": "evaluated_and_recovered", "symbol": symbol}

def trigger_recovery_protocols(symbol, storage_file):
    parser = market_portfolio_monitor.MarketParser(storage_file)
    val = parser.fetch_and_store(symbol, 100.0)
    return {"status": "triggered", "value": val}

def run_advanced_recovery_check(symbol, shifts, storage_file=None):
    reporter_obj = market_portfolio_stress_reporter.PortfolioStressReporter(storage_file or "storage.db")
    res = reporter_obj.run_stress_report(symbol, shifts)
    return res

def safe_recovery_execution(symbol, url, telegram_token, chat_id, storage_file):
    return market_portfolio_monitor.run_pipeline(symbol, url, telegram_token, chat_id, storage_file)

def run_stress_recovery_bridge_pipeline(symbol, url, telegram_token, chat_id, storage_file, shifts=None):
    market_portfolio_monitor.run_pipeline(symbol, url, telegram_token, chat_id, storage_file)
    reporter = market_portfolio_stress_reporter.StressReporter(storage_file)
    if shifts is not None:
        reporter.run_stress_reporting(symbol, shifts)
    else:
        market_portfolio_stress_reporter.run_stress_reporting_pipeline(storage_file, symbol, [0.0])
    return {"status": "bridge_pipeline_completed", "symbol": symbol}

class MarketStressRecoveryBridge:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def execute_recovery(self):
        return {"status": "executed"}

    def run_pipeline(self):
        return {"status": "pipeline_run"}