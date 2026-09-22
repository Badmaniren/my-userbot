import os
import json
from skills import market_portfolio_alert_filter_router
from skills import market_portfolio_alert_dispatcher

AlertFilterRouter = market_portfolio_alert_filter_router.AlertFilterRouter

def handle_portfolio_alert_event(symbol, url, token, chat_id, storage, severity, threshold, channels):
    return market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
        symbol, url, token, chat_id, storage, severity, threshold, channels
    )

def process_incoming_stream(alert_id):
    return market_portfolio_alert_dispatcher.process_stream_alert(alert_id)

def route_and_sink_alerts(storage, symbol, url, token, chat_id, severity, threshold, channels):
    try:
        router = AlertFilterRouter(storage=storage)
    except TypeError:
        router = AlertFilterRouter(storage)
    return router.route_filtered_alerts(symbol, url, token, chat_id, severity, threshold, channels)

def load_sink_stream_data(storage):
    try:
        router = AlertFilterRouter(storage=storage)
    except TypeError:
        router = AlertFilterRouter(storage)
    return router.load_stream_data()

def process_event_sink_trigger(symbol, url, telegram_token, chat_id, storage_file, severity_level, min_threshold, channels):
    dispatch_res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
        symbol, url, telegram_token, chat_id, storage_file, severity_level, min_threshold, channels
    )
    
    try:
        router = AlertFilterRouter(storage=storage_file)
    except TypeError:
        try:
            router = AlertFilterRouter(storage_file=storage_file)
        except TypeError:
            router = AlertFilterRouter(storage_file)
            
    try:
        router.route_filtered_alerts(symbol, url, telegram_token, chat_id, severity_level, min_threshold, channels)
    except TypeError:
        pass
    
    if not os.path.exists(storage_file):
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        with open(storage_file, "w", encoding="utf-8") as f:
            json.dump({"symbol": symbol, "status": "processed"}, f)
    else:
        with open(storage_file, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
            if not isinstance(data, dict):
                data = {}
            data["symbol"] = symbol
            data["status"] = "processed"
            f.seek(0)
            json.dump(data, f)
            f.truncate()
            
    return {
        "status": "success",
        "symbol": symbol,
        "dispatch_result": dispatch_res
    }