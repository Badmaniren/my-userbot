import requests
from typing import Dict, Any, Optional

from skills.db_storage import DbStorage as db_storage
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway

class VarPublisherException(Exception):
    """Исключение, возникающее при ошибках публикации отчетов VaR."""
    pass

class MarketPortfolioVarWebPublisher:
    """Класс для публикации VaR и отчетов о рисках портфеля во внешние веб-хуки или по API."""

    def __init__(self, webhook_url: str, api_token: Optional[str] = None):
        self.webhook_url = webhook_url
        self.api_token = api_token

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def publish_var_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Публикует отчет о VaR на веб-хук."""
        try:
            headers = self._get_headers()
            response = requests.post(self.webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise VarPublisherException(f"HTTP error occurred: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            raise VarPublisherException(f"Failed to publish VaR report: {req_err}") from req_err

    def stream_risk_metrics(self, stream_data: Any) -> Dict[str, Any]:
        """Потоковая передача метрик риска."""
        try:
            headers = self._get_headers()
            data = stream_data.read() if hasattr(stream_data, "read") else stream_data
            response = requests.post(self.webhook_url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as req_err:
            raise VarPublisherException(f"Failed to stream risk metrics: {req_err}") from req_err

    def verify_webhook_connection(self) -> bool:
        """Проверяет доступность и корректность веб-хука."""
        health_url = f"{self.webhook_url}/health"
        headers = self._get_headers()
        try:
            response = requests.get(health_url, headers=headers, timeout=10)
            response.raise_for_status()
            return bool(response.text)
        except requests.exceptions.RequestException:
            return False


def market_portfolio_var_web_publisher(
    portfolio_id: str,
    webhook_url: str,
    var_data: Dict[str, Any],
    api_token: Optional[str] = None
) -> Dict[str, Any]:
    """Функция-обертка для интеграционного сценария."""
    publisher = MarketPortfolioVarWebPublisher(webhook_url=webhook_url, api_token=api_token)
    payload = {
        "portfolio_id": portfolio_id,
        "var_data": var_data
    }

    res = publisher.publish_var_report(payload)
    published_id = res.get("id", portfolio_id)
    status = res.get("status", "success")

    return {
        "published_id": published_id,
        "portfolio_id": portfolio_id,
        "target_webhook": webhook_url,
        "status": status
    }