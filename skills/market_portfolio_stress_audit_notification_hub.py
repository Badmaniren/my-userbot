import io
from skills import (
    market_portfolio_telegram_notifier,
    market_portfolio_webhook_sync,
    market_portfolio_api_gateway,
    market_portfolio_stress_audit_summary_vault,
    db_storage
)

def start_new(target_channel: str, payload: dict, notifier_type: str) -> dict:
    """
    Централизованная маршрутизация и отправка уведомлений для юнит-тестов (интеграционный интерфейс).
    """
    return start_v2(target_channel, payload, notifier_type)


def start_v2(target_channel: str, payload: dict, notifier_type: str) -> dict:
    """
    Централизованная маршрутизация и отправка уведомлений для юнит-тестов.
    """
    if notifier_type == "telegram":
        # Поддерживаем как вызов функции (если это mock или функция), так и метод .send_notification
        if callable(market_portfolio_telegram_notifier):
            res = market_portfolio_telegram_notifier(target_channel, payload)
        else:
            res = market_portfolio_telegram_notifier.send_notification(target_channel, payload)
        db_storage.save_audit_log(payload)
        return res
    elif notifier_type == "webhook":
        if hasattr(market_portfolio_webhook_sync, "post"):
            resp_obj = market_portfolio_webhook_sync.post(target_channel, json=payload)
        else:
            resp_obj = market_portfolio_webhook_sync(target_channel, json=payload)
        db_storage.save_audit_log(payload)
        return {
            "status_code": getattr(resp_obj, "status_code", 200),
            "response_text": getattr(resp_obj, "text", str(resp_obj))
        }
    elif notifier_type == "api_gateway":
        if hasattr(market_portfolio_api_gateway, "stream_audit_payload"):
            stream_data = market_portfolio_api_gateway.stream_audit_payload(target_channel, payload)
        else:
            stream_data = market_portfolio_api_gateway(target_channel, payload)
        db_storage.save_audit_log(payload)
        content = stream_data.read() if hasattr(stream_data, "read") else (stream_data if isinstance(stream_data, bytes) else b"")
        return {
            "stream_processed": len(content) > 0,
            "content": content
        }
    else:
        raise ValueError(f"Unknown notifier type: {notifier_type}")


def market_portfolio_stress_audit_notification_hub(hub_payload: dict) -> dict:
    """
    Интеграционная функция маршрутизации и отправки уведомлений по нескольким каналам.
    """
    audit_id = hub_payload.get("audit_id")
    portfolio_id = hub_payload.get("portfolio_id")
    channels = hub_payload.get("channels", [])
    
    results = {}
    for ch in channels:
        if ch == "telegram":
            if callable(market_portfolio_telegram_notifier):
                results["telegram"] = market_portfolio_telegram_notifier({
                    "audit_id": audit_id,
                    "target": portfolio_id
                })
            else:
                results["telegram"] = market_portfolio_telegram_notifier.send_notification(portfolio_id, {"audit_id": audit_id})
        elif ch == "webhook":
            if callable(market_portfolio_webhook_sync):
                results["webhook"] = market_portfolio_webhook_sync({
                    "audit_id": audit_id,
                    "payload": hub_payload
                })
            else:
                results["webhook"] = market_portfolio_webhook_sync.post(portfolio_id, json=hub_payload)
        elif ch == "api" or ch == "api_gateway":
            if callable(market_portfolio_api_gateway):
                results["api"] = market_portfolio_api_gateway({
                    "action": "get_notification_status",
                    "audit_id": audit_id
                })
            else:
                results["api"] = market_portfolio_api_gateway.stream_audit_payload(portfolio_id, {"audit_id": audit_id})

    return {
        "dispatch_status": "success",
        "audit_id": audit_id,
        "results": results
    }