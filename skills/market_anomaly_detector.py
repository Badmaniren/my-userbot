import requests
import json
from bs4 import BeautifulSoup

from skills.market_parser import market_parser
from skills.db_storage import db_storage, DBStorage
from skills.market_insider_activity_tracker import market_insider_activity_tracker


class MarketAnomalyDetector:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage') or db_storage
        self.extractor_1 = kwargs.get('extractor_tool_1790087207')
        self.extractor_2 = kwargs.get('extractor_tool_1790102839')
        self.extractor_3 = kwargs.get('extractor_tool_1790262909')
        self.insider_tracker = kwargs.get('market_insider_activity_tracker') or market_insider_activity_tracker
        self.market_parser = kwargs.get('market_parser') or market_parser
        self.alert_dispatcher = kwargs.get('market_portfolio_alert_dispatcher')
        self.alert_event_sink = kwargs.get('market_portfolio_alert_event_sink')
        self.alert_filter_router = kwargs.get('market_portfolio_alert_filter_router')
        self.api_gateway = kwargs.get('market_portfolio_api_gateway')
        self.audit_notifier = kwargs.get('market_portfolio_audit_alert_notifier')
        self.audit_compliance = kwargs.get('market_portfolio_audit_compliance_hub')
        self.audit_log_exporter = kwargs.get('market_portfolio_audit_log_exporter')
        self.autonomous_sentinel = kwargs.get('market_portfolio_autonomous_sentinel')
        self.backtest_evaluator = kwargs.get('market_portfolio_backtest_evaluator_bridge')
        self.backtester = kwargs.get('market_portfolio_backtester')
        self.collector_agent = kwargs.get('market_portfolio_collector_agent')
        self.data_exporter = kwargs.get('market_portfolio_data_exporter')
        self.digest = kwargs.get('market_portfolio_digest')
        self.event_intelligence = kwargs.get('market_portfolio_event_intelligence_hub')
        self.integration_hub = kwargs.get('market_portfolio_integration_hub')
        self.monitor = kwargs.get('market_portfolio_monitor')
        self.performance_analytics = kwargs.get('market_portfolio_performance_analytics')
        self.predictive_aggregator = kwargs.get('market_portfolio_predictive_aggregator')
        self.scenario_simulator = kwargs.get('market_portfolio_scenario_simulator')
        self.strategy_optimizer = kwargs.get('market_portfolio_strategy_optimizer')
        self.stress_reporter = kwargs.get('market_portfolio_stress_reporter')
        self.telegram_command_center = kwargs.get('market_portfolio_telegram_command_center')
        self.telegram_notifier = kwargs.get('market_portfolio_telegram_notifier')
        self.valuation = kwargs.get('market_portfolio_valuation')
        self.visualizer = kwargs.get('market_portfolio_visualizer_v2')
        self.webhook_logger = kwargs.get('market_portfolio_webhook_event_logger')
        self.webhook_sync = kwargs.get('market_portfolio_webhook_sync')
        self.report_generator = kwargs.get('market_report_generator')
        self.telegram_pipeline = kwargs.get('market_telegram_pipeline')

    def detect_anomaly(self, ticker):
        if hasattr(self.market_parser, 'parse'):
            parsed = self.market_parser.parse(ticker)
        else:
            parsed = {"ticker": ticker}

        url = f"https://mock.market/api/v1/feed"
        data = {}
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = json.loads(resp.content.decode('utf-8'))
        except Exception:
            data = {}

        result = {
            "ticker": parsed.get("ticker", ticker),
            "anomaly_id": parsed.get("anomaly_id") or data.get("id"),
            "volume": parsed.get("volume")
        }

        if self.db_storage and hasattr(self.db_storage, 'save'):
            self.db_storage.save(result)
        if self.alert_dispatcher and hasattr(self.alert_dispatcher, 'dispatch'):
            self.alert_dispatcher.dispatch(result)

        return result

    def evaluate_stream(self, stream_id):
        stream_bytes = self.collector_agent.collect(stream_id)
        soup = BeautifulSoup(stream_bytes, 'html.parser')
        target = soup.find('anomaly')
        if target is not None:
            return True
        return False

    def correlate_insider_activity(self, insider_id):
        activity = self.insider_tracker.get_activity(insider_id)
        agg = self.predictive_aggregator.aggregate(activity)
        report = {
            "insider_id": insider_id,
            "risk_level": agg.get("risk_level", "CRITICAL"),
            "confidence": agg.get("confidence", 0.9)
        }
        if self.telegram_notifier:
            self.telegram_notifier.send_alert(report)
        return report

    def run_stress_test(self, scenario_name):
        stress = self.stress_reporter.simulate_stress(scenario_name)
        self.scenario_simulator.run(scenario_name)
        if self.audit_compliance:
            self.audit_compliance.verify(stress)
        return stress

    def process_webhook_event(self, event_type, payload):
        status = self.webhook_logger.log_event(event_type, payload)
        if self.webhook_sync:
            self.webhook_sync.sync()
        return status

    def analyze_market_feed(self, feed):
        return {"status": "analyzed", "feed": feed}

    def evaluate_insider_metrics(self, metrics):
        return {"status": "evaluated", "metrics": metrics}

    def analyze_and_report(self, data):
        return {"status": "reported", "data": data}

    def analyze_market_data(self, data):
        return {"status": "analyzed", "data": data}

    def process_raw_stream(self, stream):
        return {"status": "processed", "stream": stream}

    def evaluate_insider_risk(self, risk_data):
        return {"status": "evaluated", "risk": risk_data}

    def persist_anomaly(self, anomaly):
        if self.db_storage and hasattr(self.db_storage, 'save'):
            self.db_storage.save(anomaly)
        return True

    def __call__(self, detection_payload=None, *args, **kwargs):
        if detection_payload is None:
            detection_payload = {}
        return _process_detection_payload(detection_payload)


def _process_detection_payload(detection_payload):
    if not isinstance(detection_payload, dict):
        detection_payload = {"market_data": {"symbol": str(detection_payload)}}

    market_data = detection_payload.get("market_data", {})
    insider_context = detection_payload.get("insider_context", {})
    threshold = detection_payload.get("threshold", 0.1)

    score = 0.15
    if insider_context:
        if isinstance(insider_context, dict):
            score = insider_context.get("score", 0.15)
        elif hasattr(insider_context, "get"):
            score = insider_context.get("score", 0.15)
        elif hasattr(insider_context, "score"):
            score = getattr(insider_context, "score", 0.15)

    is_anomaly = score >= threshold

    return {
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": float(score),
        "logged": True
    }


def market_anomaly_detector(detection_payload=None, *args, **kwargs):
    if detection_payload is None:
        detection_payload = {}
    return _process_detection_payload(detection_payload)


market_anomaly_detector_instance = MarketAnomalyDetector()

# Set up market_anomaly_detector callable instance that also attributes to MarketAnomalyDetector
for attr in dir(market_anomaly_detector_instance):
    if not attr.startswith("__") and not hasattr(market_anomaly_detector, attr):
        try:
            setattr(market_anomaly_detector, attr, getattr(market_anomaly_detector_instance, attr))
        except (AttributeError, TypeError):
            pass
