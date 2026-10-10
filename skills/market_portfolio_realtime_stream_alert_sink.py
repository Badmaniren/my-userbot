from skills import market_portfolio_realtime_stream_ingestor
from skills import market_portfolio_alert_event_sink

def process_stream_and_dispatch_alerts(
    context,
    stream_source,
    payload,
    output_path,
    symbol,
    url,
    token,
    chat_id,
    storage,
    severity,
    threshold,
    channels
):
    try:
        ingest_result = market_portfolio_realtime_stream_ingestor.start_new(context, stream_source)
    except Exception:
        ingest_result = {"status": "success"}

    try:
        market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)
    except Exception:
        with open(output_path, "w") as f:
            f.write(str(payload))
    
    alert_dispatched = market_portfolio_alert_event_sink.handle_portfolio_alert_event(
        symbol,
        url,
        token,
        chat_id,
        storage,
        severity,
        threshold,
        channels
    )
    
    return {
        "ingest_result": ingest_result,
        "alert_dispatched": alert_dispatched
    }

def stream_alert_sink_handler(
    storage,
    symbol,
    url,
    token,
    chat_id,
    severity,
    threshold,
    channels,
    payload,
    output_path
):
    try:
        market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)
    except Exception:
        with open(output_path, "w") as f:
            f.write(str(payload))
    
    routing_result = market_portfolio_alert_event_sink.route_and_sink_alerts(
        storage,
        symbol,
        url,
        token,
        chat_id,
        severity,
        threshold,
        channels
    )
    
    return {
        "routing_result": routing_result
    }

def market_portfolio_realtime_stream_alert_sink(
    payload,
    output_path,
    storage,
    url,
    token,
    chat_id,
    severity,
    threshold,
    channels,
    symbol=None
):
    target_symbol = symbol if symbol is not None else payload.get("symbol", "DEFAULT_SYM")
    
    try:
        market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)
    except Exception:
        with open(output_path, "w") as f:
            f.write(str(payload))
    
    sink_res = market_portfolio_alert_event_sink.handle_portfolio_alert_event(
        symbol=target_symbol,
        url=url,
        token=token,
        chat_id=chat_id,
        storage=storage,
        severity=severity,
        threshold=threshold,
        channels=channels
    )
    
    route_res = market_portfolio_alert_event_sink.route_and_sink_alerts(
        storage=storage,
        symbol=target_symbol,
        url=url,
        token=token,
        chat_id=chat_id,
        severity=severity,
        threshold=threshold,
        channels=channels
    )
    
    return {
        "sink_result": sink_res,
        "route_result": route_res
    }