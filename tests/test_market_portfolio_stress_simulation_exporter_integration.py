import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.market_portfolio_stress_simulation_exporter import (
    market_portfolio_stress_simulation_exporter
)
from skills.market_portfolio_stress_scenario_pipeline import (
    market_portfolio_stress_scenario_pipeline
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine
)
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioStressSimulationExporter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.portfolio_id = str(uuid.uuid4())
        self.simulation_id = str(uuid.uuid4())
        self.shock_factor = round(random.uniform(0.05, 0.5), 4)
        self.iterations = random.randint(100, 1000)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_stress_simulation_export_pipeline(self):
        scenario_data = market_portfolio_stress_scenario_pipeline(
            portfolio_id=self.portfolio_id,
            shock_factor=self.shock_factor
        )
        self.assertIsNotNone(scenario_data)

        monte_carlo_result = market_portfolio_stress_monte_carlo_engine(
            portfolio_id=self.portfolio_id,
            iterations=self.iterations,
            scenario_payload=scenario_data
        )
        self.assertIsNotNone(monte_carlo_result)

        db_storage(
            record_id=self.simulation_id,
            data=monte_carlo_result,
            namespace="stress_simulation_results"
        )

        export_formats = ["json", "csv", "html"]
        for fmt in export_formats:
            export_path = os.path.join(self.test_dir, f"report_{self.simulation_id}.{fmt}")

            export_result = market_portfolio_stress_simulation_exporter(
                simulation_id=self.simulation_id,
                output_format=fmt,
                destination_path=export_path
            )

            self.assertTrue(export_result, f"Export failed for format: {fmt}")
            self.assertTrue(os.path.exists(export_path), f"Export file not created for format: {fmt}")

            file_size = os.path.getsize(export_path)
            self.assertGreater(file_size, 0, f"Export file is empty for format: {fmt}")

if __name__ == "__main__":
    unittest.main()