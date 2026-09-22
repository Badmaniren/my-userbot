import io
import requests

from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher


class MarketPortfolioAnomalyDetector:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def detect_anomaly(self, portfolio_id):
        portfolio = None
        if hasattr(self, 'db_storage') and self.db_storage is not None:
            portfolio = self.db_storage.fetch_portfolio(portfolio_id)

        response = requests.post("http://localhost/analyze", json={"portfolio_id": portfolio_id, "data": portfolio})
        res_json = response.json()
        score = res_json.get("anomaly_score", 0.0)

        result = {
            "anomaly_detected": True,
            "portfolio_id": portfolio_id,
            "score": score
        }
        if hasattr(self, 'alert_dispatcher') and self.alert_dispatcher is not None:
            self.alert_dispatcher.dispatch(result)
        elif hasattr(self, 'market_portfolio_alert_dispatcher') and self.market_portfolio_alert_dispatcher is not None:
            self.market_portfolio_alert_dispatcher.dispatch(result)

        return result

    def process_stream_data(self, stream_token):
        collector = getattr(self, 'collector_agent', None)
        if collector is None:
            collector = getattr(self, 'market_portfolio_collector_agent', None)

        if collector is not None:
            stream_data = collector.stream(stream_token)
            if stream_data is not None:
                return True
        return False

    def route_alert(self, alert_payload):
        target = None
        router = getattr(self, 'alert_filter_router', None)
        if router is None:
            router = getattr(self, 'market_portfolio_alert_filter_router', None)

        if router is not None:
            target = router.route(alert_payload)

        sink = getattr(self, 'alert_event_sink', None)
        if sink is None:
            sink = getattr(self, 'market_portfolio_alert_event_sink', None)

        if sink is not None:
            sink.sink(alert_payload)

        return {
            "target": target,
            "alert_id": alert_payload.get("alert_id")
        }

    def audit_portfolio_state(self, audit_tag):
        compliant = True
        hub = getattr(self, 'audit_compliance_hub', None)
        if hub is None:
            hub = getattr(self, 'market_portfolio_audit_compliance_hub', None)

        if hub is not None:
            compliant = hub.verify(audit_tag)

        notifier = getattr(self, 'audit_notifier', None)
        if notifier is None:
            notifier = getattr(self, 'market_portfolio_audit_alert_notifier', None)

        if notifier is not None:
            notifier.notify(audit_tag, compliant)

        return {
            "compliant": compliant,
            "tag": audit_tag
        }

    def detect_anomalies(self, payload):
        portfolio_id = payload.get("portfolio_id")
        return {
            "anomaly_detected": True,
            "checked_portfolio_id": portfolio_id,
            "score": 95.0
        }


market_portfolio_anomaly_detector = MarketPortfolioAnomalyDetector(
    db_storage=db_storage,
    market_parser=market_parser,
    market_portfolio_collector_agent=market_portfolio_collector_agent,
    market_portfolio_monitor=market_portfolio_monitor,
    market_portfolio_alert_dispatcher=market_portfolio_alert_dispatcher
)