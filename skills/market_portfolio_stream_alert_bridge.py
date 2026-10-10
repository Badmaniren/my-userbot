from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor, start_new
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts, send_telegram_notification

def process_stream_and_dispatch(
    payload,
    output_path,
    symbol,
    url,
    telegram_token,
    chat_id,
    storage_file,
    severity_level,
    min_threshold,
    channels
):
    stream_processing = market_portfolio_realtime_stream_ingestor(payload, output_path)
    
    alert_dispatch_status = None
    alert_dispatched = False
    
    if stream_processing.get("anomaly_detected", False):
        alert_dispatch_status = dispatch_portfolio_alerts(
            symbol,
            url,
            telegram_token,
            chat_id,
            storage_file,
            severity_level,
            min_threshold,
            channels
        )
        alert_dispatched = True
    else:
        alert_dispatched = False

    return {
        "stream_processing": stream_processing,
        "alert_dispatch_status": alert_dispatch_status,
        "alert_dispatched": alert_dispatched
    }

def evaluate_stream_anomaly_bridge(
    context,
    stream_source,
    telegram_token,
    chat_id,
    alert_message_template
):
    start_result = start_new(context, stream_source)
    source_id = start_result.get("source_id", "")
    
    message = f"{alert_message_template} - {source_id}"
    send_telegram_notification(telegram_token, chat_id, message)
    
    return start_result

def process_stream_and_dispatch_alert(
    context,
    stream_source,
    payload,
    output_path,
    url,
    telegram_token,
    chat_id,
    storage_file,
    severity_level,
    min_threshold,
    channels
):
    start_new(context, stream_source)
    
    symbol = payload.get("symbol", "TEST_SYMBOL")
    stream_result = market_portfolio_realtime_stream_ingestor(payload, output_path)
    
    dispatched = False
    dispatch_res = None
    if stream_result.get("anomaly_detected", True):
        dispatch_res = dispatch_portfolio_alerts(
            symbol,
            url,
            telegram_token,
            chat_id,
            storage_file,
            severity_level,
            min_threshold,
            channels
        )
        dispatched = True

    return {
        "status": "success",
        "event_id": payload.get("event_id"),
        "stream_processing": stream_result,
        "alert_dispatch_status": dispatch_res,
        "dispatched": dispatched
    }