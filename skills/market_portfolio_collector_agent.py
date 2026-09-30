import os
import json
from datetime import datetime


class MarketParser:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def fetch_and_store(self, symbol: str, price: float) -> None:
        data = []
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = []
        
        entry = {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.utcnow().isoformat()
        }
        data.append(entry)
        
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class PortfolioValuation:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def get_total_summary(self, url: str) -> dict:
        return {"summary": "ok", "url": url}


class PortfolioDigestManager:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def compile_digest(self, symbol: str, url: str) -> dict:
        return {"digest": f"digest for {symbol}", "url": url}


class PortfolioScenarioSimulator:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def simulate_scenario(self, symbol: str, percentage_shift: float) -> dict:
        return {"symbol": symbol, "shift": percentage_shift, "result": "simulated"}


class StressReporter:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def get_stream_data(self) -> list:
        return [{"stream": "data"}]


class PortfolioVisualizer:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def build_text_report(self, symbol: str) -> str:
        return f"Report for {symbol}"


class MarketPortfolioCollectorAgent:
    def __init__(self, storage_file: str = "default.json"):
        self.storage_file = storage_file

    def fetch_live_data(self, *args, **kwargs):
        return {"status": "live", "data": "stream"}

    def collect_market_data(self, *args, **kwargs):
        return {"status": "collected"}

    def collect_portfolio_data(self, portfolio_id=None, *args, **kwargs):
        return {"portfolio_id": portfolio_id, "data": []}


market_portfolio_collector_agent = MarketPortfolioCollectorAgent()


def get_historical_returns(*args, **kwargs):
    return [0.01, -0.02, 0.015]


def save_historical_returns(*args, **kwargs):
    return True


def collect_market_data(*args, **kwargs):
    return market_portfolio_collector_agent.collect_market_data(*args, **kwargs)


def collect_portfolio_data(portfolio_id=None, *args, **kwargs):
    return market_portfolio_collector_agent.collect_portfolio_data(portfolio_id=portfolio_id, *args, **kwargs)


def run_pipeline(symbol: str, url: str, telegram_token: str, chat_id: str, storage_file: str) -> bool:
    parser = MarketParser(storage_file)
    if not os.path.exists(storage_file):
        parser.fetch_and_store(symbol, 100.0)
    
    valuation = PortfolioValuation(storage_file)
    valuation.get_total_summary(url)
    
    digest_manager = PortfolioDigestManager(storage_file)
    digest_manager.compile_digest(symbol, url)
    
    simulator = PortfolioScenarioSimulator(storage_file)
    simulator.simulate_scenario(symbol, 5.0)
    
    stress_reporter = StressReporter(storage_file)
    stress_reporter.get_stream_data()
    
    visualizer = PortfolioVisualizer(storage_file)
    visualizer.build_text_report(symbol)
    
    return True


def start_new(symbol: str = None, url: str = None, telegram_token: str = None, chat_id: str = None, storage_file: str = "default.json", *args, **kwargs) -> bool:
    if symbol and url and telegram_token and chat_id:
        return run_pipeline(
            symbol,
            url,
            telegram_token,
            chat_id,
            storage_file
        )
    return True
