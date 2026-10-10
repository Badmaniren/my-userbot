from websockets.sync.client import connect


def start_new(*args, **kwargs):
    url = kwargs.get("url") or kwargs.get("feed_source") or kwargs.get("endpoint")
    if not url and args:
        url = args[0]
    if not url:
        url = "wss://market-stream.io/default"

    timeout = kwargs.get("timeout", 5.0)
    auth_token = kwargs.get("auth_token")
    symbol = kwargs.get("symbol")

    with connect(url, timeout=timeout) as ws:
        if auth_token:
            ws.send(f'{{"auth": "{auth_token}"}}')
        
        response = ws.recv()
        if symbol and symbol in response:
            return {"symbol": symbol}
        return response


def market_portfolio_realtime_websocket_feed(payload):
    if not isinstance(payload, dict):
        payload = {}
    
    feed_uuid = payload.get("feed_uuid")
    return {
        "status": "connected",
        "feed_uuid": feed_uuid,
        "symbol": payload.get("symbol"),
        "price": payload.get("price"),
        "volume": payload.get("volume")
    }