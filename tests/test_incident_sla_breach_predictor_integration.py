import unittest
import io
import os
import uuid
import random
from skills.incident_sla_breach_predictor import IncidentSLABreachPredictor, incident_sla_breach_predictor
from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer

class TestIncidentSLABreachPredictorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_incident_id = uuid.uuid4().hex
        self.severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.output_file = f"sla_prediction_{self.test_incident_id}.json"

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass

    def test_predictor_class_stream_and_prediction(self):
        random_severity = random.choice(self.severities)
        random_response_time = round(random.uniform(1.0, 50.0), 2)

        predictor = IncidentSLABreachPredictor(historical_data=[{"sev": random_severity, "rt": random_response_time}])

        single_result = predictor.predict_breach(random_severity, random_response_time)
        self.assertEqual(single_result["severity"], random_severity)
        self.assertEqual(single_result["response_time"], random_response_time)
        self.assertIn("risk_score", single_result)
        self.assertIn("will_breach", single_result)

        stream_data = f"{random_severity},{random_response_time}\nCRITICAL,100.0"
        stream_io = io.BytesIO(stream_data.encode('utf-8'))

        stream_results = predictor.evaluate_stream(stream_io)
        self.assertGreaterEqual(len(stream_results), 2)
        self.assertEqual(stream_results[0]["severity"], random_severity)
        self.assertEqual(stream_results[1]["severity"], "CRITICAL")

    def test_incident_sla_breach_predictor_function_and_file_generation(self):
        random_severity = random.choice(self.severities)
        random_response_time = round(random.uniform(5.0, 60.0), 2)

        payload = {
            "incident_id": self.test_incident_id,
            "severity": random_severity,
            "response_time_minutes": random_response_time
        }

        result = incident_sla_breach_predictor(payload)

        self.assertEqual(result["incident_id"], self.test_incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("probability", result)
        self.assertIn("risk_score", result)

        self.assertTrue(os.path.exists(self.output_file), f"Expected output file {self.output_file} was not created.")

    def test_connected_modules_import_and_execution(self):
        aggregator_callable = incident_aggregator
        evaluator_callable = incident_severity_evaluator
        analyzer_callable = incident_trend_analyzer

        self.assertTrue(callable(aggregator_callable))
        self.assertTrue(callable(evaluator_callable))
        self.assertTrue(callable(analyzer_callable))

        random_severity = random.choice(self.severities)
        random_response_time = round(random.uniform(2.0, 30.0), 2)

        payload = {
            "incident_id": self.test_incident_id,
            "severity": random_severity,
            "response_time_minutes": random_response_time
        }

        prediction_result = incident_sla_breach_predictor(payload)
        self.assertEqual(prediction_result["incident_id"], self.test_incident_id)

if __name__ == "__main__":
    unittest.main()