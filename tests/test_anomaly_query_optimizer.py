import unittest
from unittest.mock import patch
import os
import io
import uuid
import random
from skills.anomaly_query_optimizer import (
    QueryOptimizerError,
    QueryFilter,
    AnomalyQueryOptimizer,
    optimize_query,
    filter_logs_by_index
)


class TestAnomalyQueryOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer_id_val = uuid.uuid4().hex
        self.storage_filename = f"storage_{uuid.uuid4().hex}.log"
        self.tag_val = uuid.uuid4().hex[:8]
        self.timestamp_val = random.randint(1000000, 9999999)
        self.index_hint_val = uuid.uuid4().hex[:6]
        self.base_query = f"SELECT * FROM {uuid.uuid4().hex[:5]}"

    def tearDown(self):
        if os.path.exists(self.storage_filename):
            try:
                os.remove(self.storage_filename)
            except OSError:
                pass

    def test_query_optimizer_error_inheritance(self):
        self.assertTrue(issubclass(QueryOptimizerError, Exception))

    def test_query_filter_initialization(self):
        q_filter = QueryFilter(start_time=self.timestamp_val, tag=self.tag_val)
        self.assertEqual(q_filter.start_time, self.timestamp_val)
        self.assertEqual(q_filter.tag, self.tag_val)

    def test_optimizer_init_defaults(self):
        optimizer = AnomalyQueryOptimizer()
        self.assertIsNone(optimizer.optimizer_id)
        self.assertIsNone(optimizer.storage_path)
        self.assertFalse(optimizer.is_indexed)
        self.assertEqual(optimizer._query_cache, {})

    def test_build_index_success(self):
        optimizer = AnomalyQueryOptimizer(optimizer_id=self.optimizer_id_val)
        indexes = [uuid.uuid4().hex, uuid.uuid4().hex]
        res = optimizer.build_index(indexes)
        self.assertTrue(res)
        self.assertTrue(optimizer.is_indexed)

    def test_build_index_storage_error(self):
        non_existent_path = f"missing_{uuid.uuid4().hex}.log"
        optimizer = AnomalyQueryOptimizer(storage_path=non_existent_path)
        with self.assertRaises(QueryOptimizerError):
            optimizer.build_index([uuid.uuid4().hex])

    def test_build_index_storage_success(self):
        with open(self.storage_filename, "w") as f:
            f.write(uuid.uuid4().hex + "\n")

        optimizer = AnomalyQueryOptimizer(storage_path=self.storage_filename)
        res = optimizer.build_index([uuid.uuid4().hex])
        self.assertTrue(res)
        self.assertTrue(optimizer.is_indexed)

    def test_optimize_query_with_time_and_tag(self):
        optimizer = AnomalyQueryOptimizer()
        q_filter = QueryFilter(start_time=self.timestamp_val, tag=self.tag_val)
        optimized = optimizer.optimize_query(self.base_query, q_filter)
        self.assertIn(f"timestamp >= {self.timestamp_val}", optimized)
        self.assertIn(f"tag == '{self.tag_val}'", optimized)
        self.assertIn("WHERE", optimized)

    def test_optimize_query_with_existing_where(self):
        optimizer = AnomalyQueryOptimizer()
        query_with_where = f"{self.base_query} WHERE id = 1"
        q_filter = QueryFilter(start_time=self.timestamp_val)
        optimized = optimizer.optimize_query(query_with_where, q_filter)
        self.assertIn(" AND ", optimized)
        self.assertIn(f"timestamp >= {self.timestamp_val}", optimized)

    def test_optimize_query_no_filters(self):
        optimizer = AnomalyQueryOptimizer()
        q_filter = QueryFilter()
        optimized = optimizer.optimize_query(self.base_query, q_filter)
        self.assertEqual(optimized, self.base_query)

    def test_execute_with_storage(self):
        line_content = uuid.uuid4().hex
        with open(self.storage_filename, "wb") as f:
            f.write(f"{line_content}\n".encode('utf-8'))

        optimizer = AnomalyQueryOptimizer(storage_path=self.storage_filename)
        results = optimizer.execute(self.base_query)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["anomaly_id"], line_content)

    def test_execute_without_storage(self):
        optimizer = AnomalyQueryOptimizer()
        results = optimizer.execute(self.base_query)
        self.assertEqual(results, [])

    def test_clear_cache(self):
        optimizer = AnomalyQueryOptimizer()
        cache_key = uuid.uuid4().hex
        optimizer._query_cache[cache_key] = uuid.uuid4().hex
        self.assertTrue(len(optimizer._query_cache) > 0)
        optimizer.clear_cache()
        self.assertEqual(optimizer._query_cache, {})

    def test_parse_filters_severity_double_quotes(self):
        optimizer = AnomalyQueryOptimizer()
        sev_val = uuid.uuid4().hex[:6]
        query = f"SELECT * FROM logs severity = \"{sev_val}\""
        parsed = optimizer.parse_filters(query)
        self.assertIn('severity', parsed)
        self.assertEqual(parsed['severity'], sev_val)

    def test_parse_filters_severity_single_quotes(self):
        optimizer = AnomalyQueryOptimizer()
        sev_val = uuid.uuid4().hex[:6]
        query = f"SELECT * FROM logs severity = '{sev_val}'"
        parsed = optimizer.parse_filters(query)
        self.assertIn('severity', parsed)
        self.assertEqual(parsed['severity'], sev_val)

    def test_parse_filters_timestamp(self):
        optimizer = AnomalyQueryOptimizer()
        ts_val = random.randint(11111, 99999)
        query = f"SELECT * FROM logs timestamp > {ts_val}"
        parsed = optimizer.parse_filters(query)
        self.assertIn('timestamp', parsed)
        self.assertEqual(parsed['timestamp'], str(ts_val))

    def test_parse_filters_empty(self):
        optimizer = AnomalyQueryOptimizer()
        query = f"SELECT * FROM {uuid.uuid4().hex}"
        parsed = optimizer.parse_filters(query)
        self.assertEqual(parsed, {})

    def test_global_optimize_query_no_where(self):
        res = optimize_query(self.base_query, index_hint=self.index_hint_val)
        self.assertIn(f"WHERE index_hint = '{self.index_hint_val}'", res)

    def test_global_optimize_query_with_where(self):
        query_with_where = f"{self.base_query} WHERE 1=1"
        res = optimize_query(query_with_where, index_hint=self.index_hint_val)
        self.assertIn(f"AND index_hint = '{self.index_hint_val}'", res)

    def test_global_optimize_query_no_hint(self):
        res = optimize_query(self.base_query, index_hint=None)
        self.assertEqual(res, self.base_query)

    def test_filter_logs_by_index_match(self):
        target_index = uuid.uuid4().hex[:8]
        logs = [
            {"id": uuid.uuid4().hex, "data": target_index},
            {"id": uuid.uuid4().hex, "data": uuid.uuid4().hex}
        ]
        filtered = filter_logs_by_index(logs, target_index)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["data"], target_index)

    def test_filter_logs_by_index_no_match(self):
        target_index = uuid.uuid4().hex[:8]
        logs = [
            {"id": uuid.uuid4().hex, "data": uuid.uuid4().hex},
            {"id": uuid.uuid4().hex, "data": uuid.uuid4().hex}
        ]
        filtered = filter_logs_by_index(logs, target_index)
        self.assertEqual(filtered, [])