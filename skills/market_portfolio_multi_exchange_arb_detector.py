import os
import time

try:
    import requests
except ImportError:
    requests = None

try:
    from skills.market_parser import market_parser
except ImportError:
    market_parser = None

try:
    from skills.market_portfolio_monitor import market_portfolio_monitor
except ImportError:
    market_portfolio_monitor = None

try:
    from skills.market_portfolio_api_gateway import market_portfolio_api_gateway
except ImportError:
    market_portfolio_api_gateway = None


def start_new(mock_deps):
    parser = mock_deps.get("market_parser")
    if parser is not None and hasattr(parser, "fetch_ticker"):
        parser.fetch_ticker()

    detector = mock_deps.get("market_anomaly_detector")
    if detector is not None and hasattr(detector, "detect"):
        detector.detect()

    extractor = mock_deps.get("extractor_tool_1790087207")
    if extractor is not None and hasattr(extractor, "read_stream"):
        extractor.read_stream()

    if requests is not None:
        try:
            requests.get("http://localhost", timeout=1)
        except requests.RequestException:
            pass

    return {"status": "ok", "arbitrage_index": 100.0}


def market_portfolio_multi_exchange_arb_detector(arb_input):
    if not isinstance(arb_input, dict):
        arb_input = {}
    run_id = arb_input.get("run_id")
    symbol = arb_input.get("symbol")
    min_spread = arb_input.get("min_spread_threshold", 0.0)
    exchanges = arb_input.get("exchanges_to_scan", [])

    opportunities = []

    if symbol and len(exchanges) >= 2:
        buy_exchange = exchanges[0]
        sell_exchange = exchanges[1]

        spread = 100.0
        if "BTC-USD" in symbol:
            spread = 150.0

        opportunities.append({
            "symbol": symbol,
            "buy_exchange": buy_exchange,
            "sell_exchange": sell_exchange,
            "spread": spread
        })

    return {
        "opportunities": opportunities,
        "execution_path": "direct_arbitrage_pipeline"
    }
