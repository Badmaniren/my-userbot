import uuid
import io
import requests
from bs4 import BeautifulSoup
from skills.db_storage import db_storage
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.market_sentiment_risk_hub import market_sentiment_risk_hub

class MarketSentimentPortfolioAllocator:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage')
        self.extractor_1 = kwargs.get('extractor_tool_1790087207')
        self.extractor_2 = kwargs.get('extractor_tool_1790102839')
        self.extractor_3 = kwargs.get('extractor_tool_1790262909')
        self.anomaly_detector = kwargs.get('market_anomaly_detector')
        self.insider_tracker = kwargs.get('market_insider_activity_tracker')
        self.insider_alert = kwargs.get('market_insider_alert_pipeline')
        self.news_analyzer = kwargs.get('market_news_sentiment_analyzer')
        self.market_parser = kwargs.get('market_parser')
        self.alert_dispatcher = kwargs.get('market_portfolio_alert_dispatcher')
        self.alert_sink = kwargs.get('market_portfolio_alert_event_sink')
        self.alert_filter_router = kwargs.get('market_portfolio_alert_filter_router')
        self.api_gateway = kwargs.get('market_portfolio_api_gateway')
        self.audit_notifier = kwargs.get('market_portfolio_audit_alert_notifier')
        self.audit_compliance = kwargs.get('market_portfolio_audit_compliance_hub')
        self.audit_log_exporter = kwargs.get('market_portfolio_audit_log_exporter')
        self.autonomous_sentinel = kwargs.get('market_portfolio_autonomous_sentinel')
        self.backtest_bridge = kwargs.get('market_portfolio_backtest_evaluator_bridge')
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
        self.strategy_optimizer = kwargs.get('market_portfolio_strategy_optimizer') or kwargs.get('market_strategy_optimizer')
        self.stress_reporter = kwargs.get('market_portfolio_stress_reporter')
        self.telegram_cmd = kwargs.get('market_portfolio_telegram_command_center')
        self.telegram_notifier = kwargs.get('market_portfolio_telegram_notifier')
        self.valuation = kwargs.get('market_portfolio_valuation')
        self.visualizer_v2 = kwargs.get('market_portfolio_visualizer_v2')
        self.webhook_logger = kwargs.get('market_portfolio_webhook_event_logger')
        self.webhook_sync = kwargs.get('market_portfolio_webhook_sync')
        self.report_generator = kwargs.get('market_report_generator')
        self.sentiment_digest = kwargs.get('market_sentiment_digest')
        self.risk_alert_bridge = kwargs.get('market_sentiment_risk_alert_bridge')
        self.risk_hub = kwargs.get('market_sentiment_risk_hub')
        self.telegram_publisher = kwargs.get('market_sentiment_telegram_publisher')
        self.telegram_pipeline = kwargs.get('market_telegram_pipeline')

    def recalculate_portfolio_weights(self, portfolio_id):
        portfolio = self.db_storage.fetch_portfolio(portfolio_id)
        assets = portfolio.get('assets', [])

        for asset in assets:
            if self.news_analyzer:
                self.news_analyzer.analyze(asset)
            if self.risk_hub:
                self.risk_hub.calculate_risk(asset)

        try:
            requests.get("http://localhost", timeout=1)
        except requests.RequestException:
            pass

        if self.strategy_optimizer:
            return self.strategy_optimizer.optimize(portfolio_id)
        return {assets[0]: 1.0} if assets else {}

    def evaluate_portfolio_safety(self, portfolio_id):
        portfolio = self.db_storage.fetch_portfolio(portfolio_id)
        anomaly = self.anomaly_detector.check_anomaly(portfolio)
        if anomaly:
            msg = self.alert_dispatcher.dispatch(portfolio_id)
            BeautifulSoup(msg, 'html.parser')
            return True
        return False

    def export_allocation_audit_trail(self, stream):
        export_id = uuid.uuid4().hex
        if self.data_exporter:
            return self.data_exporter.export(stream)
        return export_id


def market_sentiment_portfolio_allocator(allocation_input):
    portfolio_id = allocation_input.get("portfolio_id")
    asset = allocation_input.get("asset")
    sentiment = allocation_input.get("sentiment", 0.0)
    risk = allocation_input.get("risk", 0.0)
    base_weight = allocation_input.get("base_weight", 0.1)

    if isinstance(sentiment, dict):
        sentiment = sentiment.get("score", 0.0)
    if isinstance(risk, dict):
        risk = risk.get("risk_score", 0.0)

    new_weight = round(base_weight * (1.0 + float(sentiment) - float(risk)), 4)
    allocation_id = f"alloc_{uuid.uuid4().hex[:8]}"

    record = {
        "allocation_id": allocation_id,
        "portfolio_id": portfolio_id,
        "asset": asset,
        "new_weight": new_weight,
        "sentiment": sentiment,
        "risk": risk
    }

    db_storage({
        "action": "set",
        "table": "portfolio_allocations",
        "id": allocation_id,
        "data": record
    })

    return {
        "allocation_id": allocation_id,
        "portfolio_id": portfolio_id,
        "new_weight": new_weight
    }
