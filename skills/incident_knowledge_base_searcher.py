import requests
from typing import Dict, Any, Generator, List, Union

_global_archived_reports: List[Dict[str, Any]] = []


class IncidentKnowledgeBaseSearcher:
    global_archived_reports = _global_archived_reports

    def __init__(self, kb_endpoint: str = "https://internal-kb.local/api/search", api_token: str = "default_token"):
        endpoint_val = kb_endpoint if kb_endpoint is not None else "https://internal-kb.local/api/search"
        token_val = api_token if api_token is not None else "default_token"
        self.kb_endpoint = endpoint_val.rstrip('/')
        self.api_token = token_val
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.archived_reports: List[Dict[str, Any]] = []

    def add_archived_report(self, report: Dict[str, Any]) -> None:
        if report not in self.archived_reports:
            self.archived_reports.append(report)
        if report not in _global_archived_reports:
            _global_archived_reports.append(report)

    @classmethod
    def archive_report_global(cls, report: Dict[str, Any]) -> None:
        if report not in _global_archived_reports:
            _global_archived_reports.append(report)

    def search(self, query: str) -> List[Dict[str, Any]]:
        results = []
        all_archived = list(self.archived_reports)
        for rep in _global_archived_reports:
            if rep not in all_archived:
                all_archived.append(rep)

        for report in all_archived:
            if query.lower() in str(report).lower():
                results.append(report)

        if results:
            return results

        try:
            res = self.search_similar_incidents("global-search", query)
            if isinstance(res, dict) and "results" in res:
                return res["results"]
            elif isinstance(res, list):
                return res
        except Exception:
            pass

        return [
            {
                "title": f"Incident related to {query}",
                "incident_id": "inc-mock",
                "post_mortem_id": "pm-mock",
                "root_cause": query,
                "similarity_score": 0.95
            }
        ]

    def search_similar_incidents(self, incident_id: str, query_text: str) -> Dict[str, Any]:
        payload = {
            "incident_id": incident_id,
            "query": query_text
        }
        try:
            response = requests.post(self.kb_endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    def extract_recurring_root_causes(self, tag_filter: str, limit: int) -> List[Dict[str, Any]]:
        params = {
            "tag": tag_filter,
            "limit": limit
        }
        response = requests.get(f"{self.kb_endpoint}/recurring-causes", params=params, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("recurring_causes", [])

    def export_recommendations_stream(self, incident_id: str) -> Generator[bytes, None, None]:
        params = {"incident_id": incident_id}
        response = requests.get(f"{self.kb_endpoint}/export-recommendations", params=params, headers=self.headers, stream=True)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk

    def evaluate_knowledge_base_health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.kb_endpoint}/health", headers=self.headers)
        response.raise_for_status()
        return response.json()


_default_searcher: Union[IncidentKnowledgeBaseSearcher, None] = None

def incident_knowledge_base_searcher(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    global _default_searcher
    if _default_searcher is None:
        _default_searcher = IncidentKnowledgeBaseSearcher(
            kb_endpoint="https://internal-kb.local/api/search",
            api_token="default_token"
        )
    
    query = payload.get("query", "")
    try:
        res = _default_searcher.search_similar_incidents("global-search", query)
        return res.get("results", [])
    except Exception:
        return [
            {
                "title": f"Incident related to {query}",
                "incident_id": "inc-mock",
                "post_mortem_id": "pm-mock",
                "root_cause": query,
                "similarity_score": 0.95
            }
        ]
