import uuid
from skills import (
    market_portfolio_stress_monte_carlo_engine,
    market_portfolio_stress_scenario_matrix_evaluator,
    market_portfolio_stress_reporter,
    market_portfolio_collector_agent,
    db_storage
)

class StressTestingDashboardAggregator:
    def __init__(self, monte_carlo=None, scenario_matrix=None, reporter=None):
        self.monte_carlo = monte_carlo
        self.scenario_matrix = scenario_matrix
        self.reporter = reporter

    def aggregate(self, portfolio_id, sim_count, confidence):
        mc_result = market_portfolio_stress_monte_carlo_engine.run_simulation(
            portfolio_id, sim_count, confidence
        )
        matrix_result = market_portfolio_stress_scenario_matrix_evaluator.evaluate(
            portfolio_id, mc_result
        )
        report_result = market_portfolio_stress_reporter.generate(
            matrix_result
        )
        return report_result

    def fetch_raw_metrics(self, portfolio_id):
        return market_portfolio_collector_agent.get_stream(portfolio_id)

    def generate_dashboard_report(self, metrics):
        return market_portfolio_stress_reporter.format_summary(metrics)

    def run_monte_carlo_analysis(self, ticker, seed):
        market_portfolio_stress_monte_carlo_engine.execute(ticker=ticker, seed=seed)


def market_portfolio_stress_testing_dashboard_aggregator_v2(portfolio_id, report_data, storage_handler):
    dashboard_id = f"dash_{uuid.uuid4().hex[:12]}"

    summary = {
        "dashboard_id": dashboard_id,
        "portfolio_id": portfolio_id,
        "status": "success",
        "report_data": report_data
    }

    if storage_handler and hasattr(storage_handler, "save"):
        storage_handler.save(dashboard_id, summary)

    return summary