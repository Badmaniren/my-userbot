import os
import json
import logging
from skills import db_storage as default_db_storage
from skills import market_report_generator as default_market_report_generator
from skills import market_portfolio_stress_audit_visualizer as default_visualizer
from skills import market_portfolio_stress_reporter as default_reporter

logger = logging.getLogger("market_portfolio_stress_audit_pdf_generator")


class MarketPortfolioStressAuditPdfGenerator:
    def __init__(self, **kwargs):
        self.db_storage_ref = kwargs.get("db_storage", default_db_storage)
        self.market_report_generator_ref = kwargs.get("market_report_generator", default_market_report_generator)
        self.visualizer_ref = kwargs.get("market_portfolio_stress_audit_visualizer", default_visualizer)
        self.reporter_ref = kwargs.get("market_portfolio_stress_reporter", default_reporter)

    def generate_pdf(self, payload=None, output_path=None, **kwargs):
        if payload is None:
            payload = kwargs.get("audit_data")

        if payload is None and hasattr(self.db_storage_ref, "fetch_audit_data"):
            payload = self.db_storage_ref.fetch_audit_data()

        if payload is None:
            raise ValueError("Audit data is missing")

        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")

        audit_id = payload.get("audit_id") or payload.get("portfolio_id") or payload.get("id")

        if output_path is None:
            if audit_id:
                output_path = f"/tmp/{audit_id}.pdf"
            else:
                output_path = "/tmp/report.pdf"

        pdf_binary = None
        if hasattr(self.market_report_generator_ref, "generate_pdf"):
            pdf_binary = self.market_report_generator_ref.generate_pdf(payload)

        if pdf_binary is None:
            pdf_str = (
                f"%PDF-1.4\n"
                f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
                f"Portfolio Stress Audit Report for {audit_id or 'Unknown'}\n"
                f"Payload: {json.dumps(payload, default=str)}\n"
            )
            pdf_binary = pdf_str.encode("utf-8")
        elif isinstance(pdf_binary, str):
            pdf_binary = pdf_binary.encode("utf-8")

        dirname = os.path.dirname(output_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(pdf_binary)

        return {
            "status": "success",
            "audit_id": audit_id,
            "pdf_path": output_path,
            "bytes_written": len(pdf_binary),
            "payload": payload,
        }

    def process(self, payload):
        return self.generate_pdf(payload)


def market_portfolio_stress_audit_pdf_generator(payload=None, **kwargs):
    generator = MarketPortfolioStressAuditPdfGenerator(**kwargs)
    return generator.generate_pdf(payload, **kwargs)


def start_new(
    db_storage=None,
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
    market_portfolio_integration_hub=None,
    market_portfolio_liquidity_scenario_analyzer=None,
    market_portfolio_monitor=None,
    market_portfolio_performance_analytics=None,
    market_portfolio_predictive_aggregator=None,
    market_portfolio_scenario_simulator=None,
    market_portfolio_slippage_model=None,
    market_portfolio_strategy_optimizer=None,
    market_portfolio_stress_audit_summary_vault=None,
    market_portfolio_stress_audit_visualizer=None,
    market_portfolio_stress_auto_rebalance_trigger=None,
    market_portfolio_stress_monte_carlo_engine=None,
    market_portfolio_stress_recovery_coordinator_bridge=None,
    market_portfolio_stress_reporter=None,
    market_portfolio_stress_scenario_matrix_evaluator=None,
    market_portfolio_stress_scenario_pipeline=None,
    market_portfolio_tax_calculator=None,
    market_portfolio_telegram_command_center=None,
    market_portfolio_telegram_notifier=None,
    market_portfolio_valuation=None,
    market_portfolio_var_liquidity_core=None,
    market_portfolio_visualizer_v2=None,
    market_portfolio_webhook_event_logger=None,
    market_portfolio_webhook_sync=None,
    market_report_generator=None,
    market_sentiment_digest=None,
    market_sentiment_risk_alert_bridge=None,
    market_sentiment_risk_hub=None,
    market_sentiment_telegram_publisher=None,
    market_telegram_pipeline=None,
    *args,
    **kwargs
):
    db_storage_ref = db_storage if db_storage is not None else default_db_storage

    audit_data = kwargs.get("audit_data") or kwargs.get("payload")
    if audit_data is None and db_storage_ref is not None:
        if hasattr(db_storage_ref, "fetch_audit_data"):
            audit_data = db_storage_ref.fetch_audit_data()
        elif hasattr(db_storage_ref, "get_audit_record"):
            audit_data = db_storage_ref.get_audit_record("latest")

    if audit_data is None:
        raise ValueError("Audit data is missing")

    market_report_gen_ref = market_report_generator if market_report_generator is not None else default_market_report_generator

    if market_report_gen_ref is None or not hasattr(market_report_gen_ref, "generate_pdf"):
        for arg in args:
            if hasattr(arg, "generate_pdf"):
                market_report_gen_ref = arg
                break

    pdf_binary = None
    if market_report_gen_ref is not None and hasattr(market_report_gen_ref, "generate_pdf"):
        pdf_binary = market_report_gen_ref.generate_pdf(audit_data)

    if pdf_binary is None:
        audit_id_label = audit_data.get("audit_id") if isinstance(audit_data, dict) else "Unknown"
        pdf_str = (
            f"%PDF-1.4\n"
            f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            f"Portfolio Stress Audit Report for {audit_id_label}\n"
            f"Data: {json.dumps(audit_data, default=str)}\n"
        )
        pdf_binary = pdf_str.encode("utf-8")
    elif isinstance(pdf_binary, str):
        pdf_binary = pdf_binary.encode("utf-8")

    audit_id = None
    if isinstance(audit_data, dict):
        audit_id = audit_data.get("audit_id") or audit_data.get("id") or audit_data.get("report_id")

    if audit_id:
        output_path = f"/tmp/{audit_id}.pdf"
    else:
        output_path = "/tmp/report.pdf"

    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(pdf_binary)

    return output_path
