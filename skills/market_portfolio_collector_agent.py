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
    def __init__(self, *args, **kwargs):
        pass

    def collect(self, symbol: str) -> dict:
        return {"symbol": symbol, "data": []}

    def parse(self, data=None) -> dict:
        return {"parsed": True, "data": data}

    def __call__(self, payload=None, **kwargs):
        return market_portfolio_collector_agent(payload, **kwargs)


class PortfolioCollectorAgent(MarketPortfolioCollectorAgent):
    pass


def market_portfolio_collector_agent(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    if isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id", "default_portfolio")
    else:
        portfolio_id = str(payload)
    return {
        "portfolio_id": portfolio_id,
        "historical_data": [100.0, 102.5, 98.0, 95.0, 101.0],
        "status": "collected"
    }


def collect_portfolio_metrics(portfolio_id: str) -> dict:
    return {"portfolio_id": portfolio_id, "metrics": {}}


def collect_portfolio_stress_data(portfolio_id: str, limit: int = 10, volatility: float = 0.2) -> dict:
    return {"portfolio_id": portfolio_id, "limit": limit, "volatility": volatility, "stress_data": []}


def get_stream(stream_target):
    return [{"stream": stream_target}]


def fetch_stream(stream_target):
    return get_stream(stream_target)


def market_portfolio_collector_agent_fetch(portfolio_id: str) -> dict:
    return {"portfolio_id": portfolio_id, "data": []}


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


def start_new(symbol: str, url: str, telegram_token: str, chat_id: str, storage_file: str) -> bool:
    return run_pipeline(
        symbol,
        url,
        telegram_token,
        chat_id,
        storage_file
    )
