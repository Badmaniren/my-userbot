import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import requests
from skills.repo_security_scanner import start_new

class TestRepoSecurityScanner(unittest.TestCase):

    def test_start_new_success_flow(self):
        rand_repo = f"https://github.com/secure/{uuid.uuid4().hex}"
        rand_token = f"tok_{uuid.uuid4().hex}"
        rand_output = f"/tmp/{uuid.uuid4().hex}.json"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_vuln_id = f"CVE-{random.randint(1000, 9999)}-{random.randint(10000, 99999)}"

        mock_response_data = {
            "status": "success",
            "repository": rand_repo,
            "vulnerabilities": [
                {
                    "id": rand_vuln_id,
                    "severity": rand_severity,
                    "description": ''.join(random.choices(string.ascii_letters + string.space, k=30))
                }
            ],
            "score": random.randint(0, 100)
        }

        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_resp.iter_content.return_value = [json.dumps(mock_response_data).encode('utf-8')]
            mock_post.return_value = mock_resp

            result = start_new(repo_url=rand_repo, api_token=rand_token, output_path=rand_output)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("repository"), rand_repo)
            self.assertIn("vulnerabilities", result)
            
            vulns = result["vulnerabilities"]
            self.assertTrue(len(vulns) > 0)
            self.assertEqual(vulns[0]["id"], rand_vuln_id)
            self.assertEqual(vulns[0]["severity"], rand_severity)
            mock_post.assert_called_once()

    def test_start_new_network_failure(self):
        rand_repo = f"git://internal.host/{uuid.uuid4().hex}.git"
        rand_token = uuid.uuid4().hex

        with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Connection lost")):
            with self.assertRaises(Exception) as context:
                start_new(repo_url=rand_repo, api_token=rand_token)
            
            self.assertTrue(len(str(context.exception)) > 0)

    def test_start_new_malformed_response_handling(self):
        rand_repo = f"repo_{uuid.uuid4().hex}"
        rand_garbage = bytes(''.join(random.choices(string.printable, k=50)), 'utf-8')

        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.raw = io.BytesIO(rand_garbage)
            mock_resp.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_resp

            result = start_new(repo_url=rand_repo)

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertEqual(result.get("status_code"), 500)

if __name__ == '__main__':
    unittest.main()