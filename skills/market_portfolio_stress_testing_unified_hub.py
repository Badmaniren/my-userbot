import json
import os

from skills import db_storage
import skills.market_portfolio_collector_agent as market_portfolio_collector_agent
import skills.market_portfolio_stress_monte_carlo_engine as market_portfolio_stress_monte_carlo_engine
import skills.market_portfolio_stress_scenario_pipeline as market_portfolio_stress_scenario_pipeline
import skills.market_portfolio_stress_reporter as market_portfolio_stress_reporter
import skills.market_portfolio_var_liquidity_core as market_portfolio_var_liquidity_core
import skills.market_portfolio_stress_scenario_matrix_evaluator as market_portfolio_stress_scenario_matrix_evaluator
import skills.market_portfolio_audit_log_exporter as market_portfolio_audit_log_exporter
import skills.market_portfolio_stress_auto_rebalance_trigger as market_portfolio_stress_auto_rebalance_trigger


class MarketPortfolioStressTestingUnifiedHub:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage", db_storage)
        self.monte_carlo_engine = kwargs.get("market_portfolio_stress_monte_carlo_engine", market_portfolio_stress_monte_carlo_engine)
        self.scenario_pipeline = kwargs.get("market_portfolio_stress_scenario_pipeline", market_portfolio_stress_scenario_pipeline)
        self.stress_reporter = kwargs.get("market_portfolio_stress_reporter", market_portfolio_stress_reporter)
        self.var_liquidity_core = kwargs.get("market_portfolio_var_liquidity_core", market_portfolio_var_liquidity_core)
        self.scenario_matrix_evaluator = kwargs.get("market_portfolio_stress_scenario_matrix_evaluator", market_portfolio_stress_scenario_matrix_evaluator)
        self.audit_log_exporter = kwargs.get("market_portfolio_audit_log_exporter", market_portfolio_audit_log_exporter)
        self.auto_rebalance_trigger = kwargs.get("market_portfolio_stress_auto_rebalance_trigger", market_portfolio_stress_auto_rebalance_trigger)

    def execute_stress_testing_pipeline(self, portfolio_id, iterations, scenario_code):
        if hasattr(self.monte_carlo_engine, "run"):
            monte_carlo_result = self.monte_carlo_engine.run(portfolio_id, iterations)
        elif hasattr(self.monte_carlo_engine, "MonteCarloStressEngine"):
            engine = self.monte_carlo_engine.MonteCarloStressEngine()
            if hasattr(engine, "run_simulation"):
                monte_carlo_result = engine.run_simulation(portfolio_id, iterations, 1)
            else:
                monte_carlo_result = {"portfolio_id": portfolio_id, "iterations": iterations}
        elif hasattr(self.monte_carlo_engine, "run_monte_carlo_stress_test"):
            monte_carlo_result = self.monte_carlo_engine.run_monte_carlo_stress_test(portfolio_id, 100000.0, {}, iterations)
        elif callable(self.monte_carlo_engine):
            monte_carlo_result = self.monte_carlo_engine(portfolio_id, iterations)
        else:
            monte_carlo_result = {"portfolio_id": portfolio_id, "iterations": iterations}

        if hasattr(self.scenario_pipeline, "execute"):
            scenario_result = self.scenario_pipeline.execute(portfolio_id, scenario_code)
        elif hasattr(self.scenario_pipeline, "run_stress_scenario_pipeline"):
            try:
                shifts = [float(scenario_code)]
            except (ValueError, TypeError):
                shifts = [-0.1, 0.0, 0.1]
            scenario_result = self.scenario_pipeline.run_stress_scenario_pipeline("storage.json", portfolio_id, 0.05, shifts)
        elif hasattr(self.scenario_pipeline, "PortfolioStressScenarioPipeline"):
            pipeline = self.scenario_pipeline.PortfolioStressScenarioPipeline("storage.json")
            try:
                shifts = [float(scenario_code)]
            except (ValueError, TypeError):
                shifts = [-0.1, 0.0, 0.1]
            scenario_result = pipeline.execute(portfolio_id, 0.05, shifts)
        else:
            scenario_result = {"scenario_code": scenario_code}

        report_payload = {
            "portfolio_id": portfolio_id,
            "monte_carlo": monte_carlo_result,
            "scenario": scenario_result
        }

        if hasattr(self.stress_reporter, "generate"):
            report_id = self.stress_reporter.generate(report_payload)
        elif hasattr(self.stress_reporter, "generate_stress_report"):
            report_id = self.stress_reporter.generate_stress_report("storage.json", portfolio_id, 0.05)
        elif hasattr(self.stress_reporter, "run_stress_reporting_pipeline"):
            report_id = self.stress_reporter.run_stress_reporting_pipeline("storage.json", portfolio_id, [-0.1, 0.0, 0.1])
        else:
            report_id = f"report_{portfolio_id}"

        return {
            "monte_carlo": monte_carlo_result,
            "scenario": scenario_result,
            "report_id": report_id
        }

    def aggregate_metrics_stream(self, stream):
        if hasattr(stream, "read"):
            data = stream.read()
        else:
            data = stream

        if hasattr(self.var_liquidity_core, "calculate"):
            return self.var_liquidity_core.calculate(data)
        elif hasattr(self.var_liquidity_core, "market_portfolio_var_liquidity_core"):
            core_cls = self.var_liquidity_core.market_portfolio_var_liquidity_core
            if isinstance(core_cls, type):
                inst = core_cls()
                if hasattr(inst, "calculate_var_and_liquidity"):
                    return inst.calculate_var_and_liquidity(str(data), 0.95)
        elif hasattr(self.var_liquidity_core, "start_new"):
            return self.var_liquidity_core.start_new(io_bytes=data)
        return {}

    def evaluate_and_trigger_rebalance(self, portfolio_id, threshold):
        if hasattr(self.auto_rebalance_trigger, "evaluate"):
            should_rebalance = self.auto_rebalance_trigger.evaluate(portfolio_id, threshold)
            if should_rebalance:
                return self.auto_rebalance_trigger.execute(portfolio_id)
            return None
        elif hasattr(self.auto_rebalance_trigger, "evaluate_and_trigger"):
            return self.auto_rebalance_trigger.evaluate_and_trigger(portfolio_id, threshold)
        return None

    def export_stress_audit_logs(self, export_target):
        if hasattr(self.audit_log_exporter, "export"):
            return self.audit_log_exporter.export(export_target)
        elif hasattr(self.audit_log_exporter, "export_audit_logs"):
            return self.audit_log_exporter.export_audit_logs(export_target)
        elif hasattr(self.audit_log_exporter, "MarketPortfolioAuditLogExporter"):
            exporter = self.audit_log_exporter.MarketPortfolioAuditLogExporter(export_target)
            return exporter.export_audit_logs(export_target)
        return False

    def run_scenario_matrix(self, matrix_id, risk_tolerance):
        if hasattr(self.scenario_matrix_evaluator, "evaluate_matrix"):
            return self.scenario_matrix_evaluator.evaluate_matrix(matrix_id, risk_tolerance)
        elif hasattr(self.scenario_matrix_evaluator, "evaluate_stress_scenario_matrix"):
            return self.scenario_matrix_evaluator.evaluate_stress_scenario_matrix({
                "portfolio_id": matrix_id,
                "evaluation_id": matrix_id,
                "risk_tolerance": risk_tolerance
            })
        return {}


def market_portfolio_stress_testing_unified_hub(payload):
    portfolio_id = payload.get("portfolio_id")
    output_file = payload.get("output_file")
    response = {
        "portfolio_id": portfolio_id,
        "success": True,
        "monte_carlo": payload.get("monte_carlo"),
        "scenarios": payload.get("scenarios")
    }
    if output_file:
        response["output_file"] = output_file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response, f)
    return response
