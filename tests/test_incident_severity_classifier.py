import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.incident_severity_classifier import IncidentSeverityClassifier

class TestIncidentSeverityClassifier(unittest.TestCase):

    def setUp(self):
        self.classifier = IncidentSeverityClassifier()

    def test_classify_critical_severity(self):
        random_component = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_freq = random.randint(100, 1000)
        random_id = uuid.uuid4().hex
        
        metadata = {
            "incident_id": random_id,
            "component": random_component,
            "frequency": random_freq,
            "impact": "system_wide"
        }

        result = self.classifier.classify(metadata)
        self.assertEqual(result, "critical", f"Failed to classify high frequency {random_component} as critical")

    def test_classify_low_severity_with_mock_data(self):
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.log"
        random_val = random.random()
        
        with patch('skills.incident_severity_classifier.system_health_telemetry_collector') as mock_telemetry:
            mock_telemetry.get_status.return_value = {"health_score": random_val}
            
            metadata = {
                "incident_id": uuid.uuid4().hex,
                "component": "minor_module",
                "frequency": 1,
                "path": random_path
            }
            
            result = self.classifier.classify(metadata)
            self.assertEqual(result, "low")
            mock_telemetry.get_status.assert_called_once()

    def test_classifier_logic_integrity(self):
        random_ids = [uuid.uuid4().hex for _ in range(3)]
        components = ["auth", "db", "network"]
        
        for i in range(3):
            metadata = {
                "incident_id": random_ids[i],
                "component": components[i],
                "frequency": random.randint(1, 50)
            }
            
            with patch('skills.incident_severity_classifier.incident_trend_analyzer') as mock_analyzer:
                mock_analyzer.get_trend.return_value = "stable"
                result = self.classifier.classify(metadata)
                
                self.assertIn(result, ["low", "medium", "high"])
                self.assertTrue(len(result) > 0)

    def test_stream_processing_simulation(self):
        random_content = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_content)
        
        with patch('skills.incident_severity_classifier.package_requirement_reader') as mock_reader:
            mock_reader.open_stream.return_value = mock_stream
            
            random_key = uuid.uuid4().hex
            metadata = {"incident_id": random_key, "source": "stream"}
            
            result = self.classifier.classify(metadata)
            self.assertIsNotNone(result)
            self.assertTrue(mock_reader.open_stream.called)

    def test_invalid_metadata_handling(self):
        random_key = uuid.uuid4().hex
        metadata = {"unknown_field": random_key}
        
        with self.assertRaises(KeyError):
            self.classifier.classify(metadata)

    def test_severity_threshold_boundary(self):
        random_comp = uuid.uuid4().hex
        # Тест пограничных значений частоты
        metadata_high = {"component": random_comp, "frequency": 999999}
        metadata_low = {"component": random_comp, "frequency": 0}
        
        res_high = self.classifier.classify(metadata_high)
        res_low = self.classifier.classify(metadata_low)
        
        self.assertNotEqual(res_high, res_low)
        self.assertEqual(res_high, "critical")

if __name__ == '__main__':
    unittest.main()