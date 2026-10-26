import os
import time
import re
from typing import List, Dict, Any, Optional

from skills.anomaly_logger import AnomalyLogger
from skills.extractor_tool_1792595633 import ExtractorTool


class QueryOptimizerError(Exception):
    """Исключение, возникающее при ошибках оптимизации запросов или построения индексов."""
    pass


class QueryFilter:
    def __init__(self, start_time: Optional[int] = None, tag: Optional[str] = None):
        self.start_time = start_time
        self.tag = tag


class AnomalyQueryOptimizer:
    def __init__(self, optimizer_id: Optional[str] = None, storage_path: Optional[str] = None):
        self.optimizer_id = optimizer_id
        self.storage_path = storage_path
        self.is_indexed = False
        self._query_cache: Dict[str, Any] = {}

    def build_index(self, indexes: List[str]) -> bool:
        if self.storage_path and not os.path.exists(self.storage_path):
            raise QueryOptimizerError(f"Storage path does not exist: {self.storage_path}")
        self.is_indexed = True
        return True

    def optimize_query(self, query: str, q_filter: QueryFilter) -> str:
        modifications = []
        if q_filter.start_time is not None:
            modifications.append(f"timestamp >= {q_filter.start_time}")
        if q_filter.tag is not None:
            modifications.append(f"tag == '{q_filter.tag}'")

        if modifications:
            if "WHERE" in query:
                optimizer_appendix = " AND " + " AND ".join(modifications)
            else:
                optimizer_appendix = " WHERE " + " AND ".join(modifications)
            return query + optimizer_appendix
        return query

    def execute(self, query: str) -> List[Dict[str, Any]]:
        results = []
        if self.storage_path and os.path.exists(self.storage_path):
            with open(self.storage_path, "rb") as f:
                for line in f:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if line_str:
                        results.append({"anomaly_id": line_str})
        return results

    def clear_cache(self) -> None:
        self._query_cache.clear()

    def parse_filters(self, query: str) -> Dict[str, str]:
        filters = {}
        if "severity" in query:
            parts = query.split("severity")
            if len(parts) > 1:
                sub = parts[1]
                for quote in ('"', "'"):
                    if quote in sub:
                        sub_parts = sub.split(quote)
                        if len(sub_parts) >= 2:
                            filters['severity'] = sub_parts[1]
                            break
        if "timestamp" in query:
            parts = query.split("timestamp")
            if len(parts) > 1:
                sub = parts[1]
                nums = re.findall(r'\d+', sub)
                if nums:
                    filters['timestamp'] = nums[0]
        return filters


def optimize_query(query: str, index_hint: Optional[str] = None) -> str:
    if index_hint:
        if "WHERE" in query:
            return f"{query} AND index_hint = '{index_hint}'"
        else:
            return f"{query} WHERE index_hint = '{index_hint}'"
    return query


def filter_logs_by_index(logs: List[Dict[str, Any]], index_value: str) -> List[Dict[str, Any]]:
    filtered = []
    for log in logs:
        log_str = str(log)
        if index_value in log_str:
            filtered.append(log)
    return filtered