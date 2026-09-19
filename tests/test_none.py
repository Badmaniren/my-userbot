import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.none import start_new

class TestArchitectInquisitorStartNew(unittest.TestCase):

    def setUp(self):
        self.rand_str_1 = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.rand_str_2 = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.rand_id = str(uuid.uuid4())
        self.rand_num = random.randint(100, 9999)

    def test_start_new_success_flow(self):
        payload_data = {
            "epic_id": self.rand_id,
            "direction": self.rand_str_1,
            "metric": self.rand_num
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = payload_data
        mock_response.raw = io.BytesIO(f"DATA_{self.rand_str_2}".encode('utf-8'))

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = start_new(epic_id=self.rand_id, proposal=self.rand_str_1)
            
            mock_post.assert_called_once()
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("epic_id"), self.rand_id)
            self.assertEqual(result.get("direction"), self.rand_str_1)
            self.assertEqual(result.get("metric"), self.rand_num)

    def test_start_new_failure_handling(self):
        fail_message = f"ERROR_{uuid.uuid4().hex}"
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = fail_message
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raw = io.BytesIO(fail_message.encode('utf-8'))

        with patch('requests.post', return_value=mock_response) as mock_post:
            with self.assertRaises(Exception):
                start_new(epic_id=self.rand_id, proposal=self.rand_str_1)
            mock_post.assert_called_once()

    def test_start_new_randomized_payload_integrity(self):
        custom_payload = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            uuid.uuid4().hex: random.randint(1, 1000)
        }

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = custom_payload
        mock_response.raw = io.BytesIO(b'chaos_stream')

        with patch('requests.post', return_value=mock_response) as mock_post:
            res = start_new(epic_id=self.rand_id, proposal=self.rand_str_2)
            self.assertEqual(res, custom_payload)
            self.assertIn(list(custom_payload.keys())[0], res)

if __name__ == '__main__':
    unittest.main()