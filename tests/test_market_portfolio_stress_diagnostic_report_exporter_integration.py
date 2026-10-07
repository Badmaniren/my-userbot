import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_diagnostic_report_exporter import market_portfolio_stress_diagnostic_report_exporter
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.db_storage import db_storage

class TestMarketPortfolioStressDiagnosticReportExporterIntegration(unittest.TestCase):
    def test_diagnostic_report_exporter_end_to_end(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        shock_percentage = round(random.uniform(-0.4, -0.1), 2)

        collector_input = {
            "portfolio_id": portfolio_id,
            "capital": initial_capital,
            "assets": ["AAPL", "GOOGL", "MSFT"]
        }
        collected_data = market_portfolio_collector_agent(collector_input)
        self.assertIsNotNone(collected_data)

        simulator_input = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "shock": shock_percentage,
            "data": collected_data
        }
        simulation_result = market_portfolio_scenario_simulator(simulator_input)
        self.assertIsNotNone(simulation_result)

        pipeline_input = {
            "scenario_id": scenario_id,
            "simulation_data": simulation_result
        }
        pipeline_result = market_portfolio_stress_scenario_pipeline(pipeline_input)
        self.assertIsNotNone(pipeline_result)

        db_payload = {
            "record_id": scenario_id,
            "portfolio_id": portfolio_id,
            "payload": pipeline_result
        }
        db_save_status = db_storage(db_payload)
        self.assertTrue(db_save_status)

        output_filepath = f"./diagnostic_report_{uuid.uuid4().hex}.pdf"
        exporter_input = {
            "scenario_id": scenario_id,
            "portfolio_id": portfolio_id,
            "output_path": output_filepath,
            "include_charts": True
        }

        export_result = market_portfolio_stress_diagnostic_report_exporter(exporter_input)

        self.assertIsInstance(export_result, dict)
        self.assertEqual(export_result.get("status"), "success")
        self.assertEqual(export_result.get("scenario_id"), scenario_id)
        self.assertTrue(os.path.exists(output_filepath))

        if os.path.exists(output_filepath):
            os.remove(output_filepath)

if __name__ == "__main__":
    unittest.main()