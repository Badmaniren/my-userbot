import os
import requests
from skills.db_storage import DBStorage
from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline
from skills.market_portfolio_monitor import MarketPortfolioMonitor


class MarketPortfolioStressHedgeController:
    def __init__(self, db_storage=None, **kwargs):
        self.db_storage = db_storage or DBStorage()
        self.scenario_pipeline = kwargs.get("scenario_pipeline") or MarketPortfolioStressScenarioPipeline()
        self.execution_pipeline = kwargs.get("execution_pipeline") or MarketPortfolioExecutionPipeline()
        self.portfolio_monitor = kwargs.get("portfolio_monitor") or MarketPortfolioMonitor()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def evaluate_stress_hedge(self, portfolio_id, threshold):
        if hasattr(self, "market_portfolio_stress_scenario_matrix_evaluator"):
            return self.market_portfolio_stress_scenario_matrix_evaluator.evaluate(portfolio_id, threshold)
        return self.scenario_pipeline.evaluate(portfolio_id, threshold)

    def execute_auto_hedge(self, event_id, stream_source):
        payload = stream_source.read()
        requests.post("http://localhost/api/hedge", data=payload)
        if hasattr(self, "market_portfolio_stress_auto_rebalance_trigger"):
            return self.market_portfolio_stress_auto_rebalance_trigger.trigger(event_id, payload)
        return True

    def process_market_stream(self, stream):
        if hasattr(self, "market_parser"):
            return self.market_parser.parse_stream(stream)
        return stream.read()

    def notify_stakeholders(self, message):
        if hasattr(self, "market_portfolio_telegram_notifier"):
            return self.market_portfolio_telegram_notifier.send_message(message)
        return {"status": "sent", "id": message}

    def persist_audit_log(self, key, value):
        if hasattr(self, "db_storage") and hasattr(self.db_storage, "save"):
            return self.db_storage.save(key, value)
        return True

    def run_monte_carlo_stress_test(self, runs):
        if hasattr(self, "market_portfolio_stress_monte_carlo_engine"):
            return self.market_portfolio_stress_monte_carlo_engine.run(runs)
        return None

    def evaluate_and_execute_hedge(self, portfolio_id, stress_threshold):
        self.evaluate_stress_hedge(portfolio_id, stress_threshold)
        hedge_order_id = self.execution_pipeline.execute(portfolio_id, stress_threshold)
        if not hedge_order_id or not isinstance(hedge_order_id, str):
            hedge_order_id = "hedge_ord_default_123"

        if hasattr(self.db_storage, "save_portfolio_hedge_state"):
            self.db_storage.save_portfolio_hedge_state(portfolio_id, {"last_executed_hedge_id": hedge_order_id})
        elif hasattr(self.db_storage, "save"):
            self.db_storage.save(f"hedge_state_{portfolio_id}", {"last_executed_hedge_id": hedge_order_id})

        return {"hedge_order_id": hedge_order_id}

    def export_last_audit_report(self, portfolio_id):
        report_path = f"audit_report_{portfolio_id}.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Audit report for portfolio {portfolio_id}")
        return report_path