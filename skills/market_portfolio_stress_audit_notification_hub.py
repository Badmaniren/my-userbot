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
    Централизованная маршрутизация и отправка уведомлений для юнит-тестов.
    """
    if notifier_type == "telegram":
        res = market_portfolio_telegram_notifier.send_notification(target_channel, payload)
        db_storage.save_audit_log(payload)
        return res
    elif notifier_type == "webhook":
        resp_obj = market_portfolio_webhook_sync.post(target_channel, json=payload)
        db_storage.save_audit_log(payload)
        return {
            "status_code": resp_obj.status_code,
            "response_text": resp_obj.text
        }
    elif notifier_type == "api_gateway":
        stream_data = market_portfolio_api_gateway.stream_audit_payload(target_channel, payload)
        db_storage.save_audit_log(payload)
        content = stream_data.read() if hasattr(stream_data, "read") else b""
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
    channels = hub_payload.get("channels", [])
    
    results = {}
    for ch in channels:
        if ch == "telegram":
            results["telegram"] = market_portfolio_telegram_notifier({
                "audit_id": audit_id,
                "target": hub_payload.get("portfolio_id")
            })
        elif ch == "webhook":
            results["webhook"] = market_portfolio_webhook_sync({
                "audit_id": audit_id,
                "payload": hub_payload
            })
        elif ch == "api":
            results["api"] = market_portfolio_api_gateway({
                "action": "get_notification_status",
                "audit_id": audit_id
            })

    return {
        "dispatch_status": "success",
        "audit_id": audit_id,
        "results": results
    }