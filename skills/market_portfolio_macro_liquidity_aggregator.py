import os

try:
    import requests
except ImportError:
    requests = None

try:
    from skills import db_storage
except ImportError:
    try:
        import db_storage
    except ImportError:
        db_storage = None

try:
    from skills import market_portfolio_collector_agent
except ImportError:
    try:
        import market_portfolio_collector_agent
    except ImportError:
        market_portfolio_collector_agent = None

try:
    from skills import market_portfolio_var_liquidity_core
except ImportError:
    try:
        from market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
    except ImportError:
        market_portfolio_var_liquidity_core = None


class MarketPortfolioMacroLiquidityAggregator:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage")
        self.extractor_1 = kwargs.get("extractor_tool_1790087207")
        self.extractor_2 = kwargs.get("extractor_tool_1790102839")
        self.extractor_3 = kwargs.get("extractor_tool_1790262909")
        self.extractor_4 = kwargs.get("extractor_tool_1790621808")
        self.market_anomaly_detector = kwargs.get("market_anomaly_detector")
        self.market_insider_activity_tracker = kwargs.get("market_insider_activity_tracker")
        self.market_insider_alert_pipeline = kwargs.get("market_insider_alert_pipeline")
        self.market_insider_anomaly_analyzer = kwargs.get("market_insider_anomaly_analyzer")
        self.market_insider_anomaly_report_bridge = kwargs.get("market_insider_anomaly_report_bridge")
        self.market_news_sentiment_analyzer = kwargs.get("market_news_sentiment_analyzer")
        self.market_parser = kwargs.get("market_parser")
        self.market_portfolio_alert_dispatcher = kwargs.get("market_portfolio_alert_dispatcher")
        self.market_portfolio_alert_event_sink = kwargs.get("market_portfolio_alert_event_sink")
        self.market_portfolio_alert_filter_router = kwargs.get("market_portfolio_alert_filter_router")
        self.market_portfolio_api_gateway = kwargs.get("market_portfolio_api_gateway")
        self.market_portfolio_audit_alert_notifier = kwargs.get("market_portfolio_audit_alert_notifier")
        self.market_portfolio_audit_compliance_hub = kwargs.get("market_portfolio_audit_compliance_hub")
        self.market_portfolio_audit_log_exporter = kwargs.get("market_portfolio_audit_log_exporter")
        self.market_portfolio_autonomous_sentinel = kwargs.get("market_portfolio_autonomous_sentinel")
        self.market_portfolio_backtest_evaluator_bridge = kwargs.get("market_portfolio_backtest_evaluator_bridge")
        self.market_portfolio_backtester = kwargs.get("market_portfolio_backtester")
        self.market_portfolio_collector_agent = kwargs.get("market_portfolio_collector_agent")
        self.market_portfolio_data_exporter = kwargs.get("market_portfolio_data_exporter")
        self.market_portfolio_digest = kwargs.get("market_portfolio_digest")
        self.market_portfolio_dividend_tracker = kwargs.get("market_portfolio_dividend_tracker")
        self.market_portfolio_event_intelligence_hub = kwargs.get("market_portfolio_event_intelligence_hub")
        self.market_portfolio_execution_cost_optimizer = kwargs.get("market_portfolio_execution_cost_optimizer")
        self.market_portfolio_execution_pipeline = kwargs.get("market_portfolio_execution_pipeline")
        self.market_portfolio_integration_hub = kwargs.get("market_portfolio_integration_hub")
        self.market_portfolio_liquidity_scenario_analyzer = kwargs.get("market_portfolio_liquidity_scenario_analyzer")
        self.market_portfolio_monitor = kwargs.get("market_portfolio_monitor")
        self.market_portfolio_performance_analytics = kwargs.get("market_portfolio_performance_analytics")
        self.market_portfolio_predictive_aggregator = kwargs.get("market_portfolio_predictive_aggregator")
        self.market_portfolio_scenario_simulator = kwargs.get("market_portfolio_scenario_simulator")
        self.market_portfolio_slippage_model = kwargs.get("market_portfolio_slippage_model")
        self.market_portfolio_strategy_optimizer = kwargs.get("market_portfolio_strategy_optimizer")
        self.market_portfolio_stress_audit_visualizer = kwargs.get("market_portfolio_stress_audit_visualizer")
        self.market_portfolio_stress_monte_carlo_engine = kwargs.get("market_portfolio_stress_monte_carlo_engine")
        self.market_portfolio_stress_recovery_coordinator_bridge = kwargs.get("market_portfolio_stress_recovery_coordinator_bridge")
        self.market_portfolio_stress_reporter = kwargs.get("market_portfolio_stress_reporter")
        self.market_portfolio_stress_scenario_pipeline = kwargs.get("market_portfolio_stress_scenario_pipeline")
        self.market_portfolio_tax_calculator = kwargs.get("market_portfolio_tax_calculator")
        self.market_portfolio_telegram_command_center = kwargs.get("market_portfolio_telegram_command_center")
        self.market_portfolio_telegram_notifier = kwargs.get("market_portfolio_telegram_notifier")
        self.market_portfolio_valuation = kwargs.get("market_portfolio_valuation")
        self.market_portfolio_var_liquidity_core = kwargs.get("market_portfolio_var_liquidity_core")
        self.market_portfolio_visualizer_v2 = kwargs.get("market_portfolio_visualizer_v2")
        self.market_portfolio_webhook_event_logger = kwargs.get("market_portfolio_webhook_event_logger")
        self.market_portfolio_webhook_sync = kwargs.get("market_portfolio_webhook_sync")
        self.market_report_generator = kwargs.get("market_report_generator")
        self.market_sentiment_digest = kwargs.get("market_sentiment_digest")
        self.market_sentiment_risk_alert_bridge = kwargs.get("market_sentiment_risk_alert_bridge")
        self.market_sentiment_risk_hub = kwargs.get("market_sentiment_risk_hub")
        self.market_sentiment_telegram_publisher = kwargs.get("market_sentiment_telegram_publisher")
        self.market_telegram_pipeline = kwargs.get("market_telegram_pipeline")

    def aggregate_macro_liquidity(self, token: str):
        if self.extractor_1:
            if hasattr(self.extractor_1, "extract") and callable(self.extractor_1.extract):
                self.extractor_1.extract()
            elif callable(self.extractor_1):
                self.extractor_1()
        if self.market_portfolio_collector_agent:
            agent = self.market_portfolio_collector_agent
            if hasattr(agent, "collect") and callable(agent.collect):
                return agent.collect(token)
            elif callable(agent):
                return agent(token)
            elif hasattr(agent, "start_new") and callable(agent.start_new):
                return agent.start_new(token, f"https://example.com/{token}", token, token, f"test_{token}.json")
            elif hasattr(agent, "run_pipeline") and callable(agent.run_pipeline):
                return agent.run_pipeline(token, f"https://example.com/{token}", token, token, f"test_{token}.json")
        return None

    def compute_stress_index(self, url: str) -> float:
        if requests is not None:
            try:
                response = requests.get(url, stream=True, timeout=10)
                raw_data = response.raw.read()
                return float(len(raw_data))
            except Exception:
                pass
        return 0.0

    def run_anomaly_pipeline(self, anomaly_id: str) -> dict:
        if self.market_anomaly_detector:
            agent = self.market_anomaly_detector
            if hasattr(agent, "analyze") and callable(agent.analyze):
                return agent.analyze(anomaly_id)
            elif callable(agent):
                return agent(anomaly_id)
        return {}

    def export_audit_logs(self, export_path: str) -> str:
        if self.market_portfolio_audit_log_exporter:
            agent = self.market_portfolio_audit_log_exporter
            if hasattr(agent, "export") and callable(agent.export):
                return agent.export(export_path)
            elif callable(agent):
                return agent(export_path)
        return ""


def market_portfolio_macro_liquidity_aggregator(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    macro_liquidity_index = payload.get("macro_liquidity_index")
    stress_factor = payload.get("stress_factor")
    audit_output_path = payload.get("audit_output_path")

    aggregated_id = f"agg_{portfolio_id}"

    record = {
        "action": "set",
        "portfolio_id": portfolio_id,
        "macro_liquidity_index": macro_liquidity_index,
        "stress_factor": stress_factor,
        "aggregated_id": aggregated_id
    }

    if db_storage is not None:
        if callable(db_storage):
            db_storage(record)
        elif hasattr(db_storage, "db_storage_handler"):
            db_storage.db_storage_handler(record)
        elif hasattr(db_storage, "save"):
            db_storage.save(portfolio_id, record)

    if audit_output_path:
        with open(audit_output_path, "w", encoding="utf-8") as f:
            f.write(f"Portfolio ID: {portfolio_id}\n")
            f.write(f"Macro Liquidity Index: {macro_liquidity_index}\n")
            f.write(f"Stress Factor: {stress_factor}\n")
            f.write(f"Aggregated ID: {aggregated_id}\n")

    return {
        "aggregated_id": aggregated_id,
        "status": "success"
    }
