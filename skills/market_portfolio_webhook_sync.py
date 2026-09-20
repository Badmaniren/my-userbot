import os
import requests
import skills.market_portfolio_alert_dispatcher as market_portfolio_alert_dispatcher
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway


def send_telegram_notification(token, chat_id, message):
    return market_portfolio_alert_dispatcher.send_telegram_notification(token, chat_id, message)


def sync_portfolio_via_webhook(webhook_url, storage_file, url, telegram_token, chat_id):
    gateway = MarketPortfolioAPIGateway(storage_file)
    summary = gateway.export_portfolio_summary(url)

    response = requests.post(webhook_url, json=summary)

    if response.status_code != 200:
        error_message = f"Webhook sync failed with status code {response.status_code}: {response.text}"
        send_telegram_notification(telegram_token, chat_id, error_message)
        return response

    return response.json()

def webhook_sync_pipeline(symbol, url, telegram_token, chat_id, storage_file):
    if storage_file:
        dir_name = os.path.dirname(os.path.abspath(storage_file))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(storage_file):
            with open(storage_file, 'w', encoding='utf-8') as f:
                f.write('{}')

    gateway = MarketPortfolioAPIGateway(storage_file)
    if hasattr(gateway, 'add_or_update_position'):
        gateway.add_or_update_position(symbol, 1.0, 100.0)

    webhook_url = "http://localhost/webhook"

    try:
        response = sync_portfolio_via_webhook(webhook_url, storage_file, url, telegram_token, chat_id)
        return response
    except Exception:
        summary = gateway.export_portfolio_summary(url)
        return summary