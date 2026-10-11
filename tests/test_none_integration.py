import unittest
import uuid
import random
import os
from skills.none import (
    db_storage,
    market_portfolio_collector_agent,
    market_portfolio_integration_hub,
    market_report_generator
)

class TestEpicCompletionIntegration(unittest.TestCase):
    def test_new_reflection_cycle_integration(self):
        unique_run_id = str(uuid.uuid4())
        test_metric_value = random.uniform(1050.5, 9999.9)
        test_file_path = f"reflection_artifact_{unique_run_id}.log"

        try:
            db_storage(key=unique_run_id, value=test_metric_value)

            collector_data = market_portfolio_collector_agent(run_id=unique_run_id, metric=test_metric_value)

            integrated_payload = market_portfolio_integration_hub(data=collector_data)

            report_output = market_report_generator(
                target_id=unique_run_id,
                payload=integrated_payload,
                output_path=test_file_path
            )

            self.assertIsNotNone(report_output)
            self.assertTrue(os.path.exists(test_file_path), "Артефакт нового цикла осмысления не был создан на диске.")

            with open(test_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
                self.assertIn(unique_run_id, file_content)
                self.assertIn(str(test_metric_value), file_content)

        finally:
            if os.path.exists(test_file_path):
                try:
                    os.remove(test_file_path)
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()