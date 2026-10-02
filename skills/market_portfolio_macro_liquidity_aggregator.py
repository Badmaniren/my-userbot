import json
import os

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from skills.db_storage import DbStorage
except ImportError:
    DbStorage = None

try:
    from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
except ImportError:
    market_portfolio_var_liquidity_core = None

try:
    from skills.market_portfolio_integration_hub import market_portfolio_integration_hub
except ImportError:
    market_portfolio_integration_hub = None


class MarketPortfolioMacroLiquidityAggregator:
    def __init__(
        self,
        db_storage,
        extractor_tool_1790087207,
        extractor_tool_1790102839,
        extractor_tool_1790262909,
        extractor_tool_1790621808,
        market_anomaly_detector,
        market_insider_activity_tracker,
        market_insider_alert_pipeline,
        market_insider_anomaly_analyzer,
        market_insider_anomaly_report_bridge,
        market_news_sentiment_analyzer,
        market_parser,
        market_portfolio_alert_dispatcher,
        market_portfolio_alert_event_sink,
        market_portfolio_alert_filter_router,
        market_portfolio_api_gateway,
        market_portfolio_audit_alert_notifier,
        market_portfolio_audit_compliance_hub,
        market_portfolio_audit_log_exporter,
        market_portfolio_autonomous_sentinel,
        market_portfolio_backtest_evaluator_bridge,
        market_portfolio_backtester,
        market_portfolio_collector_agent,
        market_portfolio_data_exporter,
        market_portfolio_digest,
        market_portfolio_dividend_tracker,
        market_portfolio_event_intelligence_hub,
        market_portfolio_execution_cost_optimizer,
        market_portfolio_execution_pipeline,
        market_portfolio_integration_hub,
        market_portfolio_monitor,
        market_portfolio_performance_analytics,
        market_portfolio_predictive_aggregator,
        market_portfolio_scenario_simulator,
        market_portfolio_slippage_model,
        market_portfolio_strategy_optimizer,
        market_portfolio_stress_audit_visualizer,
        market_portfolio_stress_monte_carlo_engine,
        market_portfolio_stress_recovery_coordinator_bridge,
        market_portfolio_stress_reporter,
        market_portfolio_stress_scenario_pipeline,
        market_portfolio_tax_calculator,
        market_portfolio_telegram_command_center,
        market_portfolio_telegram_notifier,
        market_portfolio_valuation,
        market_portfolio_var_liquidity_core,
        market_portfolio_visualizer_v2,
        market_portfolio_webhook_event_logger,
        market_portfolio_webhook_sync,
        market_report_generator,
        market_sentiment_digest,
        market_sentiment_risk_alert_bridge,
        market_sentiment_risk_hub,
        market_sentiment_telegram_publisher,
        market_telegram_pipeline
    ):
        self.db_storage = db_storage
        self.extractor_tool_1 = extractor_tool_1790087207
        self.extractor_tool_2 = extractor_tool_1790102839
        self.extractor_tool_3 = extractor_tool_1790262909
        self.extractor_tool_4 = extractor_tool_1790621808
        self.market_anomaly_detector = market_anomaly_detector
        self.market_insider_activity_tracker = market_insider_activity_tracker
        self.market_insider_alert_pipeline = market_insider_alert_pipeline
        self.market_insider_anomaly_analyzer = market_insider_anomaly_analyzer
        self.market_insider_anomaly_report_bridge = market_insider_anomaly_report_bridge
        self.market_news_sentiment_analyzer = market_news_sentiment_analyzer
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
        self.market_portfolio_dividend_tracker = market_portfolio_dividend_tracker
        self.market_portfolio_event_intelligence_hub = market_portfolio_event_intelligence_hub
        self.market_portfolio_execution_cost_optimizer = market_portfolio_execution_cost_optimizer
        self.market_portfolio_execution_pipeline = market_portfolio_execution_pipeline
        self.market_portfolio_integration_hub = market_portfolio_integration_hub
        self.market_portfolio_monitor = market_portfolio_monitor
        self.market_portfolio_performance_analytics = market_portfolio_performance_analytics
        self.market_portfolio_predictive_aggregator = market_portfolio_predictive_aggregator
        self.market_portfolio_scenario_simulator = market_portfolio_scenario_simulator
        self.market_portfolio_slippage_model = market_portfolio_slippage_model
        self.market_portfolio_strategy_optimizer = market_portfolio_strategy_optimizer
        self.market_portfolio_stress_audit_visualizer = market_portfolio_stress_audit_visualizer
        self.market_portfolio_stress_monte_carlo_engine = market_portfolio_stress_monte_carlo_engine
        self.market_portfolio_stress_recovery_coordinator_bridge = market_portfolio_stress_recovery_coordinator_bridge
        self.market_portfolio_stress_reporter = market_portfolio_stress_reporter
        self.market_portfolio_stress_scenario_pipeline = market_portfolio_stress_scenario_pipeline
        self.market_portfolio_tax_calculator = market_portfolio_tax_calculator
        self.market_portfolio_telegram_command_center = market_portfolio_telegram_command_center
        self.market_portfolio_telegram_notifier = market_portfolio_telegram_notifier
        self.market_portfolio_valuation = market_portfolio_valuation
        self.market_portfolio_var_liquidity_core = market_portfolio_var_liquidity_core
        self.market_portfolio_visualizer_v2 = market_portfolio_visualizer_v2
        self.market_portfolio_webhook_event_logger = market_portfolio_webhook_event_logger
        self.market_portfolio_webhook_sync = market_portfolio_webhook_sync
        self.market_report_generator = market_report_generator
        self.market_sentiment_digest = market_sentiment_digest
        self.market_sentiment_risk_alert_bridge = market_sentiment_risk_alert_bridge
        self.market_sentiment_risk_hub = market_sentiment_risk_hub
        self.market_sentiment_telegram_publisher = market_sentiment_telegram_publisher
        self.market_telegram_pipeline = market_telegram_pipeline

    def aggregate(self, rand_id):
        try:
            extracted_data = self.extractor_tool_1.extract(rand_id) if self.extractor_tool_1 and hasattr(self.extractor_tool_1, 'extract') else {}
            core_value = self.market_portfolio_var_liquidity_core.compute(rand_id) if self.market_portfolio_var_liquidity_core and hasattr(self.market_portfolio_var_liquidity_core, 'compute') else 0.0
            aggregated_liquidity = {
                "extracted": extracted_data,
                "core_liquidity": core_value,
                "aggregated_liquidity": True
            }
            if self.db_storage and hasattr(self.db_storage, 'save'):
                self.db_storage.save(rand_id, aggregated_liquidity)
            return aggregated_liquidity
        except Exception as e:
            if self.market_portfolio_audit_alert_notifier and hasattr(self.market_portfolio_audit_alert_notifier, 'notify'):
                self.market_portfolio_audit_alert_notifier.notify(str(e))
            raise e

    def parse_external_stream(self, url):
        if requests is None:
            raise ImportError("requests is not available")
        response = requests.get(url)
        content = getattr(response, 'content', b'')
        if BeautifulSoup is None:
            return content
        soup = BeautifulSoup(content, 'html.parser')
        return soup

    def evaluate_anomalies(self, threshold):
        if not self.market_anomaly_detector or not hasattr(self.market_anomaly_detector, 'check_anomaly'):
            return False
        is_anomaly = self.market_anomaly_detector.check_anomaly(threshold)
        if is_anomaly and self.market_portfolio_alert_dispatcher and hasattr(self.market_portfolio_alert_dispatcher, 'dispatch'):
            event_name = self.market_anomaly_detector.get_event_name() if hasattr(self.market_anomaly_detector, 'get_event_name') else "anomaly"
            self.market_portfolio_alert_dispatcher.dispatch(event_name)
        return is_anomaly

    def aggregate_macro_liquidity(self, portfolio_id, context, liquidity_data, export_path):
        result = {
            "status": "success",
            "portfolio_id": portfolio_id,
            "context": context,
            "liquidity_data": liquidity_data
        }
        with open(export_path, "w") as f:
            json.dump(result, f)

        if hasattr(self.db_storage, "save_macro_liquidity_record"):
            self.db_storage.save_macro_liquidity_record(portfolio_id, result)
        elif hasattr(self.db_storage, "save"):
            self.db_storage.save(portfolio_id, result)

        return result


market_portfolio_macro_liquidity_aggregator = MarketPortfolioMacroLiquidityAggregator(
    db_storage=DbStorage() if DbStorage is not None else None,
    extractor_tool_1790087207=None,
    extractor_tool_1790102839=None,
    extractor_tool_1790262909=None,
    extractor_tool_1790621808=None,
    market_anomaly_detector=None,
    market_insider_activity_tracker=None,
    market_insider_alert_pipeline=None,
    market_insider_anomaly_analyzer=None,
    market_insider_anomaly_report_bridge=None,
    market_news_sentiment_analyzer=None,
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
    market_portfolio_dividend_tracker=None,
    market_portfolio_event_intelligence_hub=None,
    market_portfolio_execution_cost_optimizer=None,
    market_portfolio_execution_pipeline=None,
    market_portfolio_integration_hub=market_portfolio_integration_hub,
    market_portfolio_monitor=None,
    market_portfolio_performance_analytics=None,
    market_portfolio_predictive_aggregator=None,
    market_portfolio_scenario_simulator=None,
    market_portfolio_slippage_model=None,
    market_portfolio_strategy_optimizer=None,
    market_portfolio_stress_audit_visualizer=None,
    market_portfolio_stress_monte_carlo_engine=None,
    market_portfolio_stress_recovery_coordinator_bridge=None,
    market_portfolio_stress_reporter=None,
    market_portfolio_stress_scenario_pipeline=None,
    market_portfolio_tax_calculator=None,
    market_portfolio_telegram_command_center=None,
    market_portfolio_telegram_notifier=None,
    market_portfolio_valuation=None,
    market_portfolio_var_liquidity_core=market_portfolio_var_liquidity_core,
    market_portfolio_visualizer_v2=None,
    market_portfolio_webhook_event_logger=None,
    market_portfolio_webhook_sync=None,
    market_report_generator=None,
    market_sentiment_digest=None,
    market_sentiment_risk_alert_bridge=None,
    market_sentiment_risk_hub=None,
    market_sentiment_telegram_publisher=None,
    market_telegram_pipeline=None
)