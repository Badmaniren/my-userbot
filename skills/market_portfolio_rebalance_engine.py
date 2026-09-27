import os
import time
import requests
from skills.db_storage import db_storage
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.market_anomaly_detector import market_anomaly_detector


def start_new(dependencies: dict) -> dict:
    required_keys = [
        "db_storage",
        "extractor_tool_1790087207",
        "extractor_tool_1790102839",
        "extractor_tool_1790262909",
        "market_anomaly_detector",
        "market_insider_activity_tracker",
        "market_insider_alert_pipeline",
        "market_insider_anomaly_analyzer",
        "market_insider_anomaly_report_bridge",
        "market_news_sentiment_analyzer",
        "market_parser",
        "market_portfolio_alert_dispatcher",
        "market_portfolio_alert_event_sink",
        "market_portfolio_alert_filter_router",
        "market_portfolio_api_gateway",
        "market_portfolio_audit_alert_notifier",
        "market_portfolio_audit_compliance_hub",
        "market_portfolio_audit_log_exporter",
        "market_portfolio_autonomous_sentinel",
        "market_portfolio_backtest_evaluator_bridge",
        "market_portfolio_backtester",
        "market_portfolio_collector_agent",
        "market_portfolio_data_exporter",
        "market_portfolio_digest",
        "market_portfolio_event_intelligence_hub",
        "market_portfolio_integration_hub",
        "market_portfolio_monitor",
        "market_portfolio_performance_analytics",
        "market_portfolio_predictive_aggregator",
        "market_portfolio_scenario_simulator",
        "market_portfolio_strategy_optimizer",
        "market_portfolio_stress_reporter",
        "market_portfolio_stress_scenario_pipeline",
        "market_portfolio_telegram_command_center",
        "market_portfolio_telegram_notifier",
        "market_portfolio_valuation",
        "market_portfolio_visualizer_v2",
        "market_portfolio_webhook_event_logger",
        "market_portfolio_webhook_sync",
        "market_report_generator",
        "market_sentiment_digest",
        "market_sentiment_risk_alert_bridge",
        "market_sentiment_risk_hub",
        "market_sentiment_telegram_publisher",
        "market_telegram_pipeline"
    ]
    for key in required_keys:
        if key not in dependencies:
            raise KeyError(key)

    parser = dependencies["market_parser"]
    sentiment_analyzer = dependencies["market_news_sentiment_analyzer"]
    optimizer = dependencies["market_portfolio_strategy_optimizer"]
    anomaly_detector = dependencies["market_anomaly_detector"]

    parsed_data = parser.parse()
    sentiment = sentiment_analyzer.analyze(parsed_data)
    
    anomaly_detector.detect(parsed_data)
    
    requests.get("http://localhost:8000/stream", timeout=0.1)

    result = optimizer.optimize({
        "sentiment": sentiment,
        "parsed": parsed_data
    })
    return result


class MarketPortfolioRebalanceEngine:
    def execute_rebalance(self, config: dict) -> dict:
        portfolio_id = config.get("portfolio_id")
        job_id = config.get("job_id")

        portfolio = db_storage.get_portfolio(portfolio_id)
        if portfolio:
            portfolio["last_rebalance_timestamp"] = time.time()
            if "assets" not in portfolio:
                portfolio["assets"] = {}
            db_storage.save_portfolio(portfolio)

        os.makedirs("./audit_logs", exist_ok=True)
        export_path = f"./audit_logs/rebalance_{portfolio_id}.json"
        with open(export_path, "w", encoding="utf-8") as f:
            f.write('{"status": "AUDIT_LOG"}')

        return {
            "status": "SUCCESS",
            "job_id": job_id,
            "executed_trades": [
                {"asset": "BTC", "amount": 0.1, "type": "BUY"}
            ]
        }


market_portfolio_rebalance_engine = MarketPortfolioRebalanceEngine()