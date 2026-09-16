import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.incident_knowledge_base_searcher import IncidentKnowledgeBaseSearcher

class TestIncidentKnowledgeBaseSearcher(unittest.TestCase):

    def setUp(self):
        self.kb_endpoint = f"https://{uuid.uuid4().hex}.internal/kb/search"
        self.api_token = f"token_{uuid.uuid4().hex}"
        self.searcher = IncidentKnowledgeBaseSearcher(
            kb_endpoint=self.kb_endpoint,
            api_token=self.api_token
        )

    def test_search_similar_incidents_success(self):
        incident_id = str(uuid.uuid4())
        query_text = f"Error in module {uuid.uuid4().hex} with code {random.randint(100, 999)}"
        expected_post_mortem_id = f"pm-{uuid.uuid4().hex[:8]}"
        expected_root_cause = f"Root cause: {uuid.uuid4().hex}"
        
        mock_response_data = {
            "query": query_text,
            "results": [
                {
                    "post_mortem_id": expected_post_mortem_id,
                    "similarity_score": round(random.uniform(0.85, 0.99), 2),
                    "root_cause": expected_root_cause,
                    "recommendations": [f"Fix {uuid.uuid4().hex}", f"Check {uuid.uuid4().hex}"]
                }
            ]
        }

        with patch('skills.incident_knowledge_base_searcher.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = self.searcher.search_similar_incidents(incident_id, query_text)

            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            self.assertEqual(called_url, self.kb_endpoint)
            
            called_json = mock_post.call_args[1]["json"]
            self.assertEqual(called_json["incident_id"], incident_id)
            self.assertEqual(called_json["query"], query_text)

            self.assertIn("results", result)
            self.assertEqual(len(result["results"]), 1)
            self.assertEqual(result["results"][0]["post_mortem_id"], expected_post_mortem_id)
            self.assertEqual(result["results"][0]["root_cause"], expected_root_cause)

    def test_search_similar_incidents_network_error(self):
        incident_id = str(uuid.uuid4())
        query_text = f"Timeout during {uuid.uuid4().hex}"

        with patch('skills.incident_knowledge_base_searcher.requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.RequestException(f"Network error {uuid.uuid4().hex}")

            with self.assertRaises(Exception) as ctx:
                self.searcher.search_similar_incidents(incident_id, query_text)
            
            self.assertIn("Network error", str(ctx.exception))

    def test_extract_recurring_root_causes(self):
        tag_filter = f"component-{uuid.uuid4().hex[:6]}"
        limit = random.randint(5, 50)
        
        expected_cause = f"Memory leak in {uuid.uuid4().hex}"
        mock_payload = {
            "tag": tag_filter,
            "limit": limit,
            "recurring_causes": [
                {
                    "root_cause": expected_cause,
                    "occurrence_count": random.randint(2, 20),
                    "associated_incidents": [str(uuid.uuid4()), str(uuid.uuid4())]
                }
            ]
        }

        with patch('skills.incident_knowledge_base_searcher.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_payload
            mock_get.return_value = mock_resp

            causes = self.searcher.extract_recurring_root_causes(tag_filter=tag_filter, limit=limit)

            mock_get.assert_called_once()
            called_params = mock_get.call_args[1]["params"]
            self.assertEqual(called_params["tag"], tag_filter)
            self.assertEqual(called_params["limit"], limit)

            self.assertEqual(len(causes), 1)
            self.assertEqual(causes[0]["root_cause"], expected_cause)

    def test_export_recommendations_stream(self):
        incident_id = str(uuid.uuid4())
        random_bytes = f"recommendation_stream_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream_data = io.BytesIO(random_bytes)

        with patch('skills.incident_knowledge_base_searcher.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raw = mock_stream_data
            mock_resp.iter_content = lambda chunk_size: [random_bytes]
            mock_get.return_value = mock_resp

            stream_generator = self.searcher.export_recommendations_stream(incident_id)
            chunks = list(stream_generator)
            
            combined_data = b"".join(chunks)
            self.assertEqual(combined_data, random_bytes)

    def test_evaluate_knowledge_base_health(self):
        expected_status = random.choice(["healthy", "degraded", "syncing"])
        expected_index_size = random.randint(1000, 999999)
        
        mock_telemetry = {
            "status": expected_status,
            "index_size": expected_index_size,
            "node_id": uuid.uuid4().hex
        }

        with patch('skills.incident_knowledge_base_searcher.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_telemetry
            mock_get.return_value = mock_resp

            health_info = self.searcher.evaluate_knowledge_base_health()

            self.assertEqual(health_info["status"], expected_status)
            self.assertEqual(health_info["index_size"], expected_index_size)

if __name__ == '__main__':
    unittest.main()