import time
import requests
from skills.db_storage import save_audit_record, fetch_audit_record


class MacroLiquidityGate:
    def __init__(self, macro_endpoint: str = "", timeout: int = 5):
        self.macro_endpoint = macro_endpoint
        self.timeout = timeout

    def check_liquidity(self) -> dict:
        try:
            response = requests.get(self.macro_endpoint, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return {
                "available": True,
                "liquidity_index": data.get("liquidity_index", 0.0),
                "timestamp": time.time(),
                "status": data.get("status", "active")
            }
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, requests.exceptions.RequestException, Exception) as e:
            return {
                "available": False,
                "liquidity_index": 0.0,
                "error": str(e)
            }

    def stream_macro_feed(self) -> bytes:
        response = requests.get(self.macro_endpoint, stream=True, timeout=self.timeout)
        return response.raw.read()

    def aggregate_macro_liquidity(self, data: dict = None) -> dict:
        return self.check_liquidity()

    def process_external_stream(self) -> bytes:
        return self.stream_macro_feed()

    def run_liquidity_scenario(self, scenario: dict = None) -> dict:
        return self.check_liquidity()


def check_macro_liquidity_availability(payload: dict) -> dict:
    result = {
        "available": True,
        "timestamp": time.time()
    }
    result.update(payload)
    return result


def market_portfolio_macro_liquidity_gate(payload: dict = None, **kwargs) -> dict:
    if payload is None:
        payload = kwargs
    return check_macro_liquidity_availability(payload or {})
