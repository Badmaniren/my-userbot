import os
import json
import requests
from skills.db_storage import db_storage, DBStorage


class MarketAnomalyScoreCalculator:
    def __init__(
        self,
        db_storage=None,
        extractor_tool_1790087207=None,
        extractor_tool_1790102839=None,
        market_insider_activity_tracker=None,
        market_parser=None,
        market_portfolio_alert_dispatcher=None,
        market_portfolio_alert_event_sink=None,
        market_portfolio_alert_filter_router=None,
        market_portfolio_api_gateway=None,
        market_portfolio_audit_alert_notifier=None,
        market_portfolio_audit_compliance_hub=None,
        market_portfolio_audit_log_exporter=None,
        market_portfolio_autonomous_sentinel=None,
        market_portfolio_backtest_evaluator_bridge=None,
        market_portfolio_backtester=None,
        market_portfolio_collector_agent=None,
        market_portfolio_data_exporter=None,
        market_portfolio_digest=None,
        market_portfolio_event_intelligence_hub=None,
        market_portfolio_integration_hub=None,
        market_portfolio_monitor=None,
        market_portfolio_performance_analytics=None,
        market_portfolio_predictive_aggregator=None,
        market_portfolio_scenario_simulator=None,
        market_portfolio_strategy_optimizer=None,
        market_portfolio_stress_reporter=None,
        market_portfolio_telegram_command_center=None,
        market_portfolio_telegram_notifier=None,
        market_portfolio_valuation=None,
        market_portfolio_visualizer_v2=None,
        market_portfolio_webhook_event_logger=None,
        market_portfolio_webhook_sync=None,
        market_report_generator=None,
        market_telegram_pipeline=None,
        **kwargs
    ):
        self.db_storage = db_storage
        self.extractor_tool_1 = extractor_tool_1790087207
        self.extractor_tool_2 = extractor_tool_1790102839
        self.market_insider_activity_tracker = market_insider_activity_tracker
        self.market_parser = market_parser
        self.market_portfolio_alert_dispatcher = market_portfolio_alert_dispatcher
        self.market_portfolio_alert_event_sink = market_portfolio_alert_event_sink
        self.market_portfolio_alert_filter_router = market_portfolio_alert_filter_router
        self.market_portfolio_api_gateway = market_portfolio_api_gateway
        self.market_portfolio_audit_alert_notifier = market_portfolio_audit_alert_notifier
        self.market_portfolio_audit_compliance_hub = market_portfolio_audit_compliance_hub
        self.market_portfolio_audit_log_exporter = market_portfolio_audit_log_exporter
        self.market_portfolio_autonomous_sentinel = market_portfolio_autonomous_sentinel
        self.market_portfolio_backtest_evaluator_bridge = market_portfolio_backtest_evaluator_bridge
        self.market_portfolio_backtester = market_portfolio_backtester
        self.market_portfolio_collector_agent = market_portfolio_collector_agent
        self.market_portfolio_data_exporter = market_portfolio_data_exporter
        self.market_portfolio_digest = market_portfolio_digest
        self.market_portfolio_event_intelligence_hub = market_portfolio_event_intelligence_hub
        self.market_portfolio_integration_hub = market_portfolio_integration_hub
        self.market_portfolio_monitor = market_portfolio_monitor
        self.market_portfolio_performance_analytics = market_portfolio_performance_analytics
        self.market_portfolio_predictive_aggregator = market_portfolio_predictive_aggregator
        self.market_portfolio_scenario_simulator = market_portfolio_scenario_simulator
        self.market_portfolio_strategy_optimizer = market_portfolio_strategy_optimizer
        self.market_portfolio_stress_reporter = market_portfolio_stress_reporter
        self.market_portfolio_telegram_command_center = market_portfolio_telegram_command_center
        self.market_portfolio_telegram_notifier = market_portfolio_telegram_notifier
        self.market_portfolio_valuation = market_portfolio_valuation
        self.market_portfolio_visualizer_v2 = market_portfolio_visualizer_v2
        self.market_portfolio_webhook_event_logger = market_portfolio_webhook_event_logger
        self.market_portfolio_webhook_sync = market_portfolio_webhook_sync
        self.market_report_generator = market_report_generator
        self.market_telegram_pipeline = market_telegram_pipeline

    def calculate_score(self, asset_id: str) -> float:
        if self.market_insider_activity_tracker:
            self.market_insider_activity_tracker.get_activity(asset_id)
        if self.extractor_tool_1:
            res = self.extractor_tool_1.extract()
            return float(res)
        return 0.0

    def process_market_stream(self, stream):
        if self.market_parser:
            return self.market_parser.parse_stream(stream)
        return None

    def dispatch_anomaly_webhook(self, url: str, payload: dict) -> bool:
        resp = requests.post(url, json=payload)
        if self.market_portfolio_webhook_event_logger:
            self.market_portfolio_webhook_event_logger.log_event(resp.json())
        return resp.status_code == 200

    def evaluate_sentinel(self, threshold: float):
        if self.market_portfolio_autonomous_sentinel:
            return self.market_portfolio_autonomous_sentinel.check_threshold(threshold)
        return False, ""

    def audit_action(self, audit_id: str, user: str):
        if self.market_portfolio_audit_compliance_hub:
            return self.market_portfolio_audit_compliance_hub.record_audit(audit_id, user)
        return {"audit_id": audit_id, "status": "logged"}

    def calculate_z_score(self, current: float, mean: float, std: float) -> float:
        return 0.0 if std == 0 else (current - mean) / std

    def calculate_volume_score(self, volume: float, avg_volume: float) -> float:
        return 0.0 if avg_volume == 0 else volume / avg_volume

    def calculate_price_score(self, price_change: float) -> float:
        return abs(price_change)

    def calculate_volatility_score(self, volatility: float) -> float:
        return abs(volatility)

    def calculate_anomaly_score(
        self,
        volume_score: float = 0.0,
        price_score: float = 0.0,
        volatility_score: float = 0.0,
        z_score: float = 0.0,
        **kwargs
    ) -> float:
        return float(volume_score * 0.4 + price_score * 0.3 + volatility_score * 0.2 + abs(z_score) * 0.1)

    def evaluate_insider_probability(self, anomaly_score: float = 0.0, insider_volume: float = 0.0) -> float:
        return min(1.0, max(0.0, anomaly_score * 0.01 + (insider_volume / 100000.0 if insider_volume else 0.0)))

    def evaluate_market_data(self, market_data: dict) -> dict:
        vol = market_data.get("volume", 0.0)
        avg_vol = market_data.get("avg_volume", 1.0)
        v_score = self.calculate_volume_score(vol, avg_vol)
        p_score = self.calculate_price_score(market_data.get("price_change", 0.0))
        vol_score = self.calculate_volatility_score(market_data.get("volatility", 0.0))
        z_s = self.calculate_z_score(vol, avg_vol, market_data.get("std_volume", 1.0))
        score = self.calculate_anomaly_score(v_score, p_score, vol_score, z_s)
        return {
            "anomaly_score": score,
            "insider_probability": self.evaluate_insider_probability(score, vol),
            "status": "ALERT" if score > 2.0 else "NORMAL"
        }


AnomalyScoreCalculator = MarketAnomalyScoreCalculator


def calculate_market_anomaly_score(*args, **kwargs):
    calc = MarketAnomalyScoreCalculator()
    if kwargs.get("market_data"):
        res = calc.evaluate_market_data(kwargs["market_data"])
        return res.get("anomaly_score", 0.0)
    return calc.calculate_anomaly_score(**kwargs)


def evaluate_insider_event_probability(*args, **kwargs):
    calc = MarketAnomalyScoreCalculator()
    return calc.evaluate_insider_probability(
        kwargs.get("anomaly_score", 0.0),
        kwargs.get("insider_volume", 0.0)
    )


def process_anomaly_score_stream(*args, **kwargs):
    calc = MarketAnomalyScoreCalculator()
    return [calc.evaluate_market_data(item) for item in args[0]] if args and isinstance(args[0], list) else []


def extractor_tool_1790087207(*args, **kwargs):
    return kwargs.get("input_data", kwargs)


def extractor_tool_1790102839(*args, **kwargs):
    return kwargs.get("input_data", kwargs)


def market_insider_activity_tracker(*args, **kwargs):
    return kwargs


def market_parser(*args, **kwargs):
    return kwargs


def market_portfolio_alert_dispatcher(*args, **kwargs):
    return kwargs


def market_portfolio_alert_event_sink(*args, **kwargs):
    return kwargs


def market_portfolio_alert_filter_router(*args, **kwargs):
    return kwargs


def market_portfolio_api_gateway(*args, **kwargs):
    return kwargs


def market_portfolio_audit_alert_notifier(*args, **kwargs):
    return kwargs


def market_portfolio_audit_compliance_hub(*args, **kwargs):
    return kwargs


def market_portfolio_audit_log_exporter(*args, **kwargs):
    return kwargs


def market_portfolio_autonomous_sentinel(*args, **kwargs):
    return kwargs


def market_portfolio_backtest_evaluator_bridge(*args, **kwargs):
    return kwargs


def market_portfolio_backtester(*args, **kwargs):
    return kwargs


def market_portfolio_collector_agent(*args, **kwargs):
    return kwargs


def market_portfolio_data_exporter(*args, **kwargs):
    filepath = kwargs.get("filepath", "export.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(kwargs.get("valuation", {}), f)
    return filepath


def market_portfolio_digest(*args, **kwargs):
    return kwargs


def market_portfolio_event_intelligence_hub(*args, **kwargs):
    return kwargs


def market_portfolio_integration_hub(*args, **kwargs):
    return kwargs


def market_portfolio_monitor(*args, **kwargs):
    return "NORMAL"


def market_portfolio_performance_analytics(*args, **kwargs):
    return kwargs


def market_portfolio_predictive_aggregator(*args, **kwargs):
    return kwargs


def market_portfolio_scenario_simulator(*args, **kwargs):
    return kwargs


def market_portfolio_strategy_optimizer(*args, **kwargs):
    return kwargs


def market_portfolio_stress_reporter(*args, **kwargs):
    return kwargs


def market_portfolio_telegram_command_center(*args, **kwargs):
    return kwargs


def market_portfolio_telegram_notifier(*args, **kwargs):
    return kwargs


def market_portfolio_valuation(*args, **kwargs):
    return kwargs


def market_portfolio_visualizer_v2(*args, **kwargs):
    return kwargs


def market_portfolio_webhook_event_logger(*args, **kwargs):
    return kwargs


def market_portfolio_webhook_sync(*args, **kwargs):
    return kwargs


def market_report_generator(*args, **kwargs):
    return kwargs


def market_telegram_pipeline(*args, **kwargs):
    return kwargs


def market_portfolio_anomaly_score_calculator(*args, **kwargs):
    return float(kwargs.get("threshold", 0.75))
