import unittest
import json
import os
import uuid
import random
from io import BytesIO
from skills.incident_digest_generator import IncidentDigestGenerator, start_new

class TestIncidentDigestGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.generator = IncidentDigestGenerator()
        self.test_output_path = f"test_digest_{uuid.uuid4()}.json"
        self.text_output_path = f"test_digest_{uuid.uuid4()}.txt"

    def tearDown(self):
        for path in [self.test_output_path, self.text_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_generate_digest_and_export_real_file(self):
        random_id = str(uuid.uuid4())
        random_module = f"module_{random.randint(1000, 9999)}"
        payload = {
            "digest_id": random_id,
            "module": random_module,
            "status": "aggregated"
        }

        json_result = self.generator.generate_digest(payload)
        self.assertIsNotNone(json_result)
        
        parsed = json.loads(json_result)
        self.assertEqual(parsed["digest_id"], random_id)
        self.assertEqual(parsed["module"], random_module)

        export_success = self.generator.export_digest_file(payload, self.test_output_path)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(self.test_output_path))

        with open(self.test_output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["digest_id"], random_id)

    def test_start_new_with_stream_integration(self):
        digest_name = f"digest_run_{uuid.uuid4()}"
        random_incident_id = str(uuid.uuid4())
        random_error = f"Error_{random.randint(100, 999)}"
        
        incidents_data = [{
            "incident_id": random_incident_id,
            "error": random_error,
            "module_name": "auth_service"
        }]
        
        stream_content = json.dumps(incidents_data).encode('utf-8')
        stream = BytesIO(stream_content)

        result = start_new(digest_name, stream, self.text_output_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.text_output_path))
        
        with open(self.text_output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 0)

    def test_start_new_empty_stream_triggers_fallback(self):
        digest_name = f"empty_digest_{uuid.uuid4()}"
        stream = BytesIO(b"")

        result = start_new(digest_name, stream, self.text_output_path)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()