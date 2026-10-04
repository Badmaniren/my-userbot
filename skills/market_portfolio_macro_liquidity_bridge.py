import os
import requests

# Честный импорт зависимостей (включая db_storage)
from skills.db_storage import db_storage
from skills.extractor_tool_1790087207 import extractor_tool_1790087207
from skills.extractor_tool_1790102839 import extractor_tool_1790102839
from skills.extractor_tool_1790262909 import extractor_tool_1790262909
from skills.extractor_tool_1790621808 import extractor_tool_1790621808
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_insider_activity_tracker import market_insider_activity_tracker
from skills.market_insider_alert_pipeline import market_insider_alert_pipeline
from skills.market_insider_anomaly_analyzer import market_insider_anomaly_analyzer
from skills.market_insider_anomaly_report_bridge import market_insider_anomaly_report_bridge
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.market_parser import market_parser
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.market_portfolio_alert_event_sink import market_portfolio_alert_event_sink
from skills.market_portfolio_alert_filter_router import market_portfolio_alert_filter_router
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway
from skills.market_portfolio_audit_alert_notifier import market_portfolio_audit_alert_notifier
from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
from skills.market_portfolio_audit_log_exporter import market_portfolio_audit_log_exporter
from skills.market_portfolio_autonomous_sentinel import market_portfolio_autonomous_sentinel
from skills.market_portfolio_backtest_evaluator_bridge import market_portfolio_backtest_evaluator_bridge
from skills.market_portfolio_backtester import market_portfolio_backtester
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_data_exporter import market_portfolio_data_exporter
from skills.market_portfolio_digest import market_portfolio_digest
from skills.market_portfolio_dividend_tracker import market_portfolio_dividend_tracker
from skills.market_portfolio_event_intelligence_hub import market_portfolio_event_intelligence_hub
from skills.market_portfolio_execution_cost_optimizer import market_portfolio_execution_cost_optimizer
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_portfolio_performance_analytics import market_portfolio_performance_analytics
from skills.market_portfolio_predictive_aggregator import market_portfolio_predictive_aggregator
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_stress_recovery_coordinator_bridge import market_portfolio_stress_recovery_coordinator_bridge
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.market_portfolio_telegram_command_center import market_portfolio_telegram_command_center
from skills.market_portfolio_telegram_notifier import market_portfolio_telegram_notifier
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.market_portfolio_visualizer_v2 import market_portfolio_visualizer_v2
from skills.market_portfolio_webhook_event_logger import market_portfolio_webhook_event_logger
from skills.market_portfolio_webhook_sync import market_portfolio_webhook_sync
from skills.market_report_generator import market_report_generator
from skills.market_sentiment_digest import market_sentiment_digest
from skills.market_sentiment_risk_alert_bridge import market_sentiment_risk_alert_bridge
from skills.market_sentiment_risk_hub import market_sentiment_risk_hub
from skills.market_sentiment_telegram_publisher import market_sentiment_telegram_publisher
from skills.market_telegram_pipeline import market_telegram_pipeline

class MarketPortfolioMacroLiquidityBridge:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage', db_storage)
        self.extractor_tool_1 = kwargs.get('extractor_tool_1790087207', extractor_tool_1790087207)
        self.extractor_tool_2 = kwargs.get('extractor_tool_1790102839', extractor_tool_1790102839)
        self.extractor_tool_3 = kwargs.get('extractor_tool_1790262909', extractor_tool_1790262909)
        self.extractor_tool_4 = kwargs.get('extractor_tool_1790621808', extractor_tool_1790621808)
        self.market_anomaly_detector = kwargs.get('market_anomaly_detector', market_anomaly_detector)
        self.market_insider_activity_tracker = kwargs.get('market_insider_activity_tracker', market_insider_activity_tracker)
        self.market_insider_alert_pipeline = kwargs.get('market_insider_alert_pipeline', market_insider_alert_pipeline)
        self.market_insider_anomaly_analyzer = kwargs.get('market_insider_anomaly_analyzer', market_insider_anomaly_analyzer)
        self.market_insider_anomaly_report_bridge = kwargs.get('market_insider_anomaly_report_bridge', market_insider_anomaly_report_bridge)
        self.market_news_sentiment_analyzer = kwargs.get('market_news_sentiment_analyzer', market_news_sentiment_analyzer)
        self.market_parser = kwargs.get('market_parser', market_parser)
        self.market_portfolio_alert_dispatcher = kwargs.get('market_portfolio_alert_dispatcher', market_portfolio_alert_dispatcher)
        self.market_portfolio_alert_event_sink = kwargs.get('market_portfolio_alert_event_sink', market_portfolio_alert_event_sink)
        self.market_portfolio_alert_filter_router = kwargs.get('market_portfolio_alert_filter_router', market_portfolio_alert_filter_router)
        self.market_portfolio_api_gateway = kwargs.get('market_portfolio_api_gateway', market_portfolio_api_gateway)
        self.market_portfolio_audit_alert_notifier = kwargs.get('market_portfolio_audit_alert_notifier', market_portfolio_audit_alert_notifier)
        self.market_portfolio_audit_compliance_hub = kwargs.get('market_portfolio_audit_compliance_hub', market_portfolio_audit_compliance_hub)
        self.market_portfolio_audit_log_exporter = kwargs.get('market_portfolio_audit_log_exporter', market_portfolio_audit_log_exporter)
        self.market_portfolio_autonomous_sentinel = kwargs.get('market_portfolio_autonomous_sentinel', market_portfolio_autonomous_sentinel)
        self.market_portfolio_backtest_evaluator_bridge = kwargs.get('market_portfolio_backtest_evaluator_bridge', market_portfolio_backtest_evaluator_bridge)
        self.market_portfolio_backtester = kwargs.get('market_portfolio_backtester', market_portfolio_backtester)
        self.market_portfolio_collector_agent = kwargs.get('market_portfolio_collector_agent', market_portfolio_collector_agent)
        self.market_portfolio_data_exporter = kwargs.get('market_portfolio_data_exporter', market_portfolio_data_exporter)
        self.market_portfolio_digest = kwargs.get('market_portfolio_digest', market_portfolio_digest)
        self.market_portfolio_dividend_tracker = kwargs.get('market_portfolio_dividend_tracker', market_portfolio_dividend_tracker)
        self.market_portfolio_event_intelligence_hub = kwargs.get('market_portfolio_event_intelligence_hub', market_portfolio_event_intelligence_hub)
        self.market_portfolio_execution_cost_optimizer = kwargs.get('market_portfolio_execution_cost_optimizer', market_portfolio_execution_cost_optimizer)
        self.market_portfolio_execution_pipeline = kwargs.get('market_portfolio_execution_pipeline', market_portfolio_execution_pipeline)
        self.market_portfolio_integration_hub = kwargs.get('market_portfolio_integration_hub', market_portfolio_integration_hub)
        self.market_portfolio_liquidity_scenario_analyzer = kwargs.get('market_portfolio_liquidity_scenario_analyzer', market_portfolio_liquidity_scenario_analyzer)
        self.market_portfolio_monitor = kwargs.get('market_portfolio_monitor', market_portfolio_monitor)
        self.market_portfolio_performance_analytics = kwargs.get('market_portfolio_performance_analytics', market_portfolio_performance_analytics)
        self.market_portfolio_predictive_aggregator = kwargs.get('market_portfolio_predictive_aggregator', market_portfolio_predictive_aggregator)
        self.market_portfolio_scenario_simulator = kwargs.get('market_portfolio_scenario_simulator', market_portfolio_scenario_simulator)
        self.market_portfolio_slippage_model = kwargs.get('market_portfolio_slippage_model', market_portfolio_slippage_model)
        self.market_portfolio_strategy_optimizer = kwargs.get('market_portfolio_strategy_optimizer', market_portfolio_strategy_optimizer)
        self.market_portfolio_stress_audit_visualizer = kwargs.get('market_portfolio_stress_audit_visualizer', market_portfolio_stress_audit_visualizer)
        self.market_portfolio_stress_monte_carlo_engine = kwargs.get('market_portfolio_stress_monte_carlo_engine', market_portfolio_stress_monte_carlo_engine)
        self.market_portfolio_stress_recovery_coordinator_bridge = kwargs.get('market_portfolio_stress_recovery_coordinator_bridge', market_portfolio_stress_recovery_coordinator_bridge)
        self.market_portfolio_stress_reporter = kwargs.get('market_portfolio_stress_reporter', market_portfolio_stress_reporter)
        self.market_portfolio_stress_scenario_pipeline = kwargs.get('market_portfolio_stress_scenario_pipeline', market_portfolio_stress_scenario_pipeline)
        self.market_portfolio_tax_calculator = kwargs.get('market_portfolio_tax_calculator', market_portfolio_tax_calculator)
        self.market_portfolio_telegram_command_center = kwargs.get('market_portfolio_telegram_command_center', market_portfolio_telegram_command_center)
        self.market_portfolio_telegram_notifier = kwargs.get('market_portfolio_telegram_notifier', market_portfolio_telegram_notifier)
        self.market_portfolio_valuation = kwargs.get('market_portfolio_valuation', market_portfolio_valuation)
        self.market_portfolio_var_liquidity_core = kwargs.get('market_portfolio_var_liquidity_core', market_portfolio_var_liquidity_core)
        self.market_portfolio_visualizer_v2 = kwargs.get('market_portfolio_visualizer_v2', market_portfolio_visualizer_v2)
        self.market_portfolio_webhook_event_logger = kwargs.get('market_portfolio_webhook_event_logger', market_portfolio_webhook_event_logger)
        self.market_portfolio_webhook_sync = kwargs.get('market_portfolio_webhook_sync', market_portfolio_webhook_sync)
        self.market_report_generator = kwargs.get('market_report_generator', market_report_generator)
        self.market_sentiment_digest = kwargs.get('market_sentiment_digest', market_sentiment_digest)
        self.market_sentiment_risk_alert_bridge = kwargs.get('market_sentiment_risk_alert_bridge', market_sentiment_risk_alert_bridge)
        self.market_sentiment_risk_hub = kwargs.get('market_sentiment_risk_hub', market_sentiment_risk_hub)
        self.market_sentiment_telegram_publisher = kwargs.get('market_sentiment_telegram_publisher', market_sentiment_telegram_publisher)
        self.market_telegram_pipeline = kwargs.get('market_telegram_pipeline', market_telegram_pipeline)

    def synchronize_macro_liquidity(self, portfolio_id: str):
        db_res = self.db_storage.fetch(portfolio_id)
        liquidity_score = self.market_portfolio_var_liquidity_core.calculate(portfolio_id, db_res)
        response = requests.get(f"https://example.com/api/macro")
        macro_data = response.json()
        macro_value = macro_data.get("macro_factor", 1.0)
        return {
            "portfolio_id": portfolio_id,
            "liquidity_score": liquidity_score,
            "macro_value": macro_value
        }

    def process_macro_stream(self, stream):
        return self.market_parser.parse_stream(stream)

    def evaluate_and_dispatch_anomalies(self, threshold: float):
        anomaly = self.market_anomaly_detector.detect(threshold)
        dispatched = self.market_portfolio_alert_dispatcher.dispatch(anomaly)
        return {
            "anomaly_id": anomaly.get("anomaly_id"),
            "dispatched": dispatched
        }

    def export_audit_logs_bridge(self, export_path: str):
        audit_logs = self.db_storage.get_audit_logs()
        path = self.market_portfolio_audit_log_exporter.export(audit_logs)
        with open(export_path, "w") as f:
            f.write(str(audit_logs))
        return path

    def send_telegram_alert(self, chat_id: str, message: str):
        return self.market_telegram_pipeline.send_message(chat_id, message)