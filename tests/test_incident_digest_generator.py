import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_digest_generator import start_new


class TestIncidentDigestGenerator(unittest.TestCase):

    def setUp(self):
        self.random_string = lambda length: ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        self.incident_id_1 = str(uuid.uuid4())
        self.incident_id_2 = str(uuid.uuid4())
        self.module_name = self.random_string(10)
        self.error_message = self.random_string(25)
        self.severity_level = random.choice(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])

    def test_start_new_digest_success(self):
        dynamic_digest_name = f"digest_{self.random_string(8)}"
        dynamic_file_path = f"/tmp/{self.random_string(12)}.json"
        
        mock_incidents = [
            {
                "incident_id": self.incident_id_1,
                "module": self.module_name,
                "error": self.error_message,
                "severity": self.severity_level
            }
        ]

        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_aggregator_class, \
             with patch('skills.incident_digest_generator.NotificationTemplateEngine') as mock_engine_class, \
             with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            
            mock_aggregator_instance = mock_aggregator_class.return_value
            mock_aggregator_instance.process_and_aggregate.return_value = mock_incidents

            mock_engine_instance = mock_engine_class.return_value
            rendered_payload = f"{self.random_string(15)}_{self.incident_id_1}"
            mock_engine_instance.render_text.return_value = rendered_payload

            result = start_new(
                digest_name=dynamic_digest_name,
                incidents_stream=io.BytesIO(json.dumps(mock_incidents).encode('utf-8')),
                output_path=dynamic_file_path
            )

            self.assertTrue(result)
            mock_aggregator_instance.process_and_aggregate.assert_called_once()
            mock_engine_instance.render_text.assert_called_once()
            mock_file.assert_called_once_with(dynamic_file_path, 'w', encoding='utf-8')

    def test_start_new_digest_empty_stream(self):
        dynamic_digest_name = f"empty_{self.random_string(6)}"
        dynamic_file_path = f"/var/log/{self.random_string(10)}.html"

        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_aggregator_class, \
             with patch('skills.incident_digest_generator.NotificationTemplateEngine') as mock_engine_class:
            
            mock_aggregator_instance = mock_aggregator_class.return_value
            mock_aggregator_instance.process_and_aggregate.return_value = []

            mock_engine_instance = mock_engine_class.return_value
            mock_engine_instance.render_html.return_value = f"<html>{self.random_string(20)}</html>"

            result = start_new(
                digest_name=dynamic_digest_name,
                incidents_stream=io.BytesIO(b''),
                output_path=dynamic_file_path
            )

            self.assertFalse(result)
            mock_aggregator_instance.process_and_aggregate.assert_called_once()

    def test_start_new_digest_exception_handling(self):
        dynamic_digest_name = f"faulty_{self.random_string(7)}"
        dynamic_file_path = f"./{self.random_string(8)}.log"

        with patch('skills.incident_digest_generator.IncidentAggregator') as mock_aggregator_class:
            mock_aggregator_instance = mock_aggregator_class.return_value
            mock_aggregator_instance.process_and_aggregate.side_effect = Exception(self.error_message)

            result = start_new(
                digest_name=dynamic_digest_name,
                incidents_stream=io.BytesIO(self.random_string(50).encode('utf-8')),
                output_path=dynamic_file_path
            )

            self.assertIsNone(result)
            mock_aggregator_instance.process_and_aggregate.assert_called_once()


if __name__ == '__main__':
    unittest.main()