import unittest
import io
import uuid
import random
from skills.incident_auto_escalation_engine import escalate_incident, evaluate_and_escalate
from skills.incident_aggregator import incident_aggregator

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):

    def test_escalate_incident_real_flow(self):
        random_id = f"INC-{uuid.uuid4()}"
        system_names = ["auth-service", "payment-gateway", "database-cluster", "cache-node"]
        severities = ["CRITICAL", "HIGH", "EMERGENCY"]

        system_name = random.choice(system_names)
        severity = random.choice(severities)

        result = escalate_incident(random_id, system_name, severity)

        self.assertIsNotNone(result, "Функция эскалации должна возвращать результат от incident_aggregator")

    def test_evaluate_and_escalate_real_stream_flow(self):
        random_id = f"INC-{uuid.uuid4()}"
        threshold = random.randint(50, 90)
        metric_value = threshold + random.randint(1, 20)

        stream_content = f"METRIC:{random_id}:{metric_value}"
        stream_data = io.BytesIO(stream_content.encode('utf-8'))

        result = evaluate_and_escalate(stream_data, threshold)

        self.assertIsNotNone(result, "При превышении порога должен быть вызван агрегатор инцидентов")

    def test_evaluate_and_escalate_below_threshold(self):
        random_id = f"INC-{uuid.uuid4()}"
        threshold = random.randint(50, 90)
        metric_value = threshold - random.randint(1, 40)

        stream_content = f"METRIC:{random_id}:{metric_value}"
        stream_data = io.BytesIO(stream_content.encode('utf-8'))

        result = evaluate_and_escalate(stream_data, threshold)

        self.assertIsNone(result, "При значении ниже порога эскалация не должна происходить")

if __name__ == '__main__':
    unittest.main()