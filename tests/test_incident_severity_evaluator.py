import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_severity_evaluator import (
    IncidentSeverityEvaluator,
    evaluate_incident_severity
)

class TestIncidentSeverityEvaluator(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Exc_{uuid.uuid4().hex[:6]}"
        self.tb_str = f"Traceback_{uuid.uuid4().hex[:10]}"
        self.incident_id = f"inc_{uuid.uuid4().hex[:8]}"

    @patch('skills.incident_severity_evaluator.IncidentAggregator')
    @patch('skills.incident_severity_evaluator.IncidentTrendForecaster')
    def test_evaluator_composition_and_logic(self, mock_forecaster_cls, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        mock_forecaster_instance = mock_forecaster_cls.return_value

        expected_aggregation = {
            "status": f"aggregated_{uuid.uuid4().hex[:4]}",
            "incident_id": self.incident_id,
            "severity_score": random.randint(1, 50)
        }
        mock_aggregator_instance.process_and_aggregate.return_value = expected_aggregation

        expected_forecast = {
            "trend": f"trend_{uuid.uuid4().hex[:4]}",
            "risk_multiplier": round(random.uniform(1.0, 5.0), 2)
        }
        mock_forecaster_instance.forecast_future_incidents.return_value = expected_forecast

        evaluator = IncidentSeverityEvaluator()

        self.assertTrue(hasattr(evaluator, 'aggregator'))
        self.assertTrue(hasattr(evaluator, 'forecaster'))

        exc_obj = Exception(self.exception_msg)
        result = evaluator.evaluate(
            module_name=self.module_name,
            exception=exc_obj,
            traceback_str=self.tb_str,
            incident_id=self.incident_id
        )

        mock_aggregator_instance.process_and_aggregate.assert_called_once_with(
            self.module_name,
            exc_obj,
            self.tb_str,
            self.incident_id
        )
        mock_forecaster_instance.forecast_future_incidents.assert_called_once_with(self.module_name)

        self.assertIn("aggregation", result)
        self.assertIn("forecast", result)
        self.assertIn("final_severity_index", result)
        self.assertEqual(result["aggregation"], expected_aggregation)
        self.assertEqual(result["forecast"], expected_forecast)

    @patch('skills.incident_severity_evaluator.IncidentAggregator')
    @patch('skills.incident_severity_evaluator.IncidentTrendForecaster')
    def test_functional_wrapper(self, mock_forecaster_cls, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        mock_forecaster_instance = mock_forecaster_cls.return_value

        agg_result = {"id": self.incident_id, "load": random.randint(100, 999)}
        forecast_result = {"probability": round(random.random(), 2)}

        mock_aggregator_instance.process_and_aggregate.return_value = agg_result
        mock_forecaster_instance.forecast_trends.return_value = forecast_result

        result = evaluate_incident_severity(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.tb_str,
            incident_id=self.incident_id
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertIn("severity_rating", result)

    @patch('skills.incident_severity_evaluator.IncidentAggregator')
    @patch('skills.incident_severity_evaluator.IncidentTrendForecaster')
    def test_evaluator_stream_handling(self, mock_forecaster_cls, mock_aggregator_cls):
        mock_forecaster_instance = mock_forecaster_cls.return_value
        random_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(random_bytes)

        expected_stream_forecast = {
            "stream_status": f"processed_{uuid.uuid4().hex[:4]}",
            "metric": random.randint(10, 100)
        }
        mock_forecaster_instance.process_stream_and_forecast.return_value = expected_stream_forecast

        evaluator = IncidentSeverityEvaluator()
        result = evaluator.evaluate_stream(self.module_name, stream_mock)

        mock_forecaster_instance.process_stream_and_forecast.assert_called_once_with(
            self.module_name, stream_mock
        )
        self.assertEqual(result, expected_stream_forecast)

if __name__ == '__main__':
    unittest.main()