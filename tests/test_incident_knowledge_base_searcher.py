import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.incident_knowledge_base_searcher import (
    IncidentKnowledgeBaseSearcher,
    incident_knowledge_base_searcher
)


class TestIncidentKnowledgeBaseSearcher(unittest.TestCase):

    def setUp(self):
        self.endpoint = f"https://{uuid.uuid4().hex}.local/api"
        self.token = uuid.uuid4().hex
        self.searcher = IncidentKnowledgeBaseSearcher(kb_endpoint=self.endpoint, api_token=self.token)
        self.incident_id = uuid.uuid4().hex
        self.query_text = uuid.uuid4().hex

    def test_init_strips_trailing_slash(self):
        raw_endpoint = f"https://{uuid.uuid4().hex}.local/api/"
        searcher = IncidentKnowledgeBaseSearcher(kb_endpoint=raw_endpoint, api_token=self.token)
        self.assertEqual(searcher.kb_endpoint, raw_endpoint.rstrip('/'))
        self.assertEqual(searcher.api_token, self.token)
        self.assertEqual(searcher.headers["Authorization"], f"Bearer {self.token}")
        self.assertEqual(searcher.headers["Content-Type"], "application/json")

    def test_search_similar_incidents_success(self):
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch("skills.incident_knowledge_base_searcher.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_result
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = self.searcher.search_similar_incidents(self.incident_id, self.query_text)

            self.assertEqual(result, expected_result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], self.endpoint)
            self.assertEqual(called_kwargs["json"]["incident_id"], self.incident_id)
            self.assertEqual(called_kwargs["json"]["query"], self.query_text)
            self.assertEqual(called_kwargs["headers"], self.searcher.headers)

    def test_search_similar_incidents_network_error(self):
        import requests
        with patch("skills.incident_knowledge_base_searcher.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException(uuid.uuid4().hex)

            with self.assertRaises(Exception) as ctx:
                self.searcher.search_similar_incidents(self.incident_id, self.query_text)
            self.assertIn("Network error", str(ctx.exception))

    def test_extract_recurring_root_causes_success(self):
        tag = uuid.uuid4().hex
        limit = random.randint(1, 100)
        recurring_list = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        
        with patch("skills.incident_knowledge_base_searcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"recurring_causes": recurring_list}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.searcher.extract_recurring_root_causes(tag, limit)

            self.assertEqual(result, recurring_list)
            mock_get.assert_called_once()
            called_args, called_kwargs = mock_get.call_args
            self.assertEqual(called_args[0], f"{self.endpoint}/recurring-causes")
            self.assertEqual(called_kwargs["params"]["tag"], tag)
            self.assertEqual(called_kwargs["params"]["limit"], limit)
            self.assertEqual(called_kwargs["headers"], self.searcher.headers)

    def test_export_recommendations_stream_success(self):
        chunk_data = uuid.uuid4().bytes
        with patch("skills.incident_knowledge_base_searcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [b"", chunk_data]
            mock_get.return_value = mock_response

            chunks = list(self.searcher.export_recommendations_stream(self.incident_id))

            self.assertEqual(chunks, [chunk_data])
            mock_get.assert_called_once()
            called_args, called_kwargs = mock_get.call_args
            self.assertEqual(called_args[0], f"{self.endpoint}/export-recommendations")
            self.assertEqual(called_kwargs["params"]["incident_id"], self.incident_id)
            self.assertTrue(called_kwargs["stream"])

    def test_evaluate_knowledge_base_health_success(self):
        health_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch("skills.incident_knowledge_base_searcher.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = health_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = self.searcher.evaluate_knowledge_base_health()

            self.assertEqual(result, health_data)
            mock_get.assert_called_once()
            called_args, _ = mock_get.call_args
            self.assertEqual(called_args[0], f"{self.endpoint}/health")

    def test_global_helper_function_success(self):
        query_val = uuid.uuid4().hex
        expected_results = [{uuid.uuid4().hex: uuid.uuid4().hex}]

        with patch("skills.incident_knowledge_base_searcher.IncidentKnowledgeBaseSearcher.search_similar_incidents") as mock_search:
            mock_search.return_value = {"results": expected_results}

            res = incident_knowledge_base_searcher({"query": query_val})

            self.assertEqual(res, expected_results)
            mock_search.assert_called_once_with("global-search", query_val)

    def test_global_helper_function_fallback_on_exception(self):
        query_val = uuid.uuid4().hex

        with patch("skills.incident_knowledge_base_searcher.IncidentKnowledgeBaseSearcher.search_similar_incidents") as mock_search:
            mock_search.side_effect = Exception(uuid.uuid4().hex)

            res = incident_knowledge_base_searcher({"query": query_val})

            self.assertIsInstance(res, list)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["root_cause"], query_val)
            self.assertEqual(res[0]["incident_id"], "inc-mock")


if __name__ == "__main__":
    unittest.main()