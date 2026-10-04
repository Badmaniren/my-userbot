import os
import requests

# Честный импорт зависимостей (включая db_storage)
from skills.db_storage import db_storage
import skills.extractor_tool_1790087207 as extractor_tool_1790087207
import skills.extractor_tool_1790102839 as extractor_tool_1790102839
import skills.extractor_tool_1790262909 as extractor_tool_1790262909
import skills.extractor_tool_1790621808 as extractor_tool_1790621808
import skills.market_anomaly_detector as market_anomaly_detector
import skills.market_insider_activity_tracker as market_insider_activity_tracker
import skills.market_insider_alert_pipeline as market_insider_alert_pipeline
import skills.market_insider_anomaly_analyzer as market_insider_anomaly_analyzer
import skills.market_insider_anomaly_report_bridge as market_insider_anomaly_report_bridge
import skills.market_news_sentiment_analyzer as market_news_sentiment_analyzer
import skills.market_parser as market_parser
import skills.market_portfolio_alert_dispatcher as market_portfolio_alert_dispatcher
import skills.market_portfolio_alert_event_sink as market_portfolio_alert_event_sink
import skills.market_portfolio_alert_filter_router as market_portfolio_alert_filter_router
import skills.market_portfolio_api_gateway as market_portfolio_api_gateway
import skills.market_portfolio_audit_alert_notifier as market_portfolio_audit_alert_notifier
import skills.market_portfolio_audit_compliance_hub as market_portfolio_audit_compliance_hub
import skills.market_portfolio_audit_log_exporter as market_portfolio_audit_log_exporter
import skills.market_portfolio_autonomous_sentinel as market_portfolio_autonomous_sentinel
import skills.market_portfolio_backtest_evaluator_bridge as market_portfolio_backtest_evaluator_bridge
import skills.market_portfolio_backtester as market_portfolio_backtester
import skills.market_portfolio_collector_agent as market_portfolio_collector_agent
import skills.market_portfolio_data_exporter as market_portfolio_data_exporter
import skills.market_portfolio_digest as market_portfolio_digest
import skills.market_portfolio_dividend_tracker as market_portfolio_dividend_tracker
import skills.market_portfolio_event_intelligence_hub as market_portfolio_event_intelligence_hub
import skills.market_portfolio_execution_cost_optimizer as market_portfolio_execution_cost_optimizer
import skills.market_portfolio_execution_pipeline as market_portfolio_execution_pipeline
import skills.market_portfolio_integration_hub as market_portfolio_integration_hub
import skills.market_portfolio_liquidity_scenario_analyzer as market_portfolio_liquidity_scenario_analyzer
import skills.market_portfolio_monitor as market_portfolio_monitor
import skills.market_portfolio_performance_analytics as market_portfolio_performance_analytics
import skills.market_portfolio_predictive_aggregator as market_portfolio_predictive_aggregator
import skills.market_portfolio_scenario_simulator as market_portfolio_scenario_simulator
import skills.market_portfolio_slippage_model as market_portfolio_slippage_model
import skills.market_portfolio_strategy_optimizer as market_portfolio_strategy_optimizer
import skills.market_portfolio_stress_audit_visualizer as market_portfolio_stress_audit_visualizer
import skills.market_portfolio_stress_monte_carlo_engine as market_portfolio_stress_monte_carlo_engine
import skills.market_portfolio_stress_recovery_coordinator_bridge as market_portfolio_stress_recovery_coordinator_bridge
import skills.market_portfolio_stress_reporter as market_portfolio_stress_reporter
import skills.market_portfolio_stress_scenario_pipeline as market_portfolio_stress_scenario_pipeline
import skills.market_portfolio_tax_calculator as market_portfolio_tax_calculator
import skills.market_portfolio_telegram_command_center as market_portfolio_telegram_command_center
import skills.market_portfolio_telegram_notifier as market_portfolio_telegram_notifier
import skills.market_portfolio_valuation as market_portfolio_valuation
import skills.market_portfolio_var_liquidity_core as market_portfolio_var_liquidity_core
import skills.market_portfolio_visualizer_v2 as market_portfolio_visualizer_v2
import skills.market_portfolio_webhook_event_logger as market_portfolio_webhook_event_logger
import skills.market_portfolio_webhook_sync as market_portfolio_webhook_sync
import skills.market_report_generator as market_report_generator
import skills.market_sentiment_digest as market_sentiment_digest
import skills.market_sentiment_risk_alert_bridge as market_sentiment_risk_alert_bridge
import skills.market_sentiment_risk_hub as market_sentiment_risk_hub
import skills.market_sentiment_telegram_publisher as market_sentiment_telegram_publisher
import skills.market_telegram_pipeline as market_telegram_pipeline

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