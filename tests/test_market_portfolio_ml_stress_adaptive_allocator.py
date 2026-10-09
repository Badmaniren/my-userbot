import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from typing import Dict, Any, Optional

from skills.market_portfolio_ml_stress_adaptive_allocator import (
    MLStressAdaptiveAllocator,
    AdaptiveAllocationError
)
from skills.market_portfolio_ml_stress_evaluator import StressEvaluationError
from skills.market_portfolio_stress_auto_rebalance_trigger import StressAutoRebalanceTrigger


class TestMLStressAdaptiveAllocator(unittest.TestCase):

    def setUp(self) -> None:
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.source_url = f"https://{uuid.uuid4().hex}.com/feed"
        self.threshold = random.uniform(0.1, 0.9)
        self.confidence_level = random.uniform(0.90, 0.99)
        self.prices = [random.uniform(10.0, 1000.0) for _ in range(random.randint(5, 20))]
        
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.window_size = random.randint(10, 100)

    def test_adaptive_allocator_initialization(self) -> None:
        allocator = MLStressAdaptiveAllocator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            window_size=self.window_size
        )
        self.assertIsNotNone(allocator)
        self.assertEqual(allocator.window_size, self.window_size)

    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.MarketPortfolioMLStressEvaluator')
    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.StressAutoRebalanceTrigger')
    def test_evaluate_and_adapt_portfolio_success(self, mock_trigger_cls, mock_evaluator_cls) -> None:
        mock_evaluator_instance = mock_evaluator_cls.return_value
        expected_stress_result = {
            "portfolio_id": self.portfolio_id,
            "risk_score": random.uniform(0.0, 1.0),
            "status": "STABLE"
        }
        mock_evaluator_instance.evaluate_stress.return_value = expected_stress_result

        mock_trigger_instance = mock_trigger_cls.return_value
        expected_trigger_result = {
            "triggered": False,
            "reason": uuid.uuid4().hex
        }
        mock_trigger_instance.evaluate_and_trigger.return_value = expected_trigger_result

        allocator = MLStressAdaptiveAllocator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            window_size=self.window_size
        )

        result = allocator.evaluate_and_adapt(
            portfolio_id=self.portfolio_id,
            prices=self.prices,
            scenario_code=self.scenario_code,
            confidence_level=self.confidence_level,
            threshold=self.threshold
        )

        self.assertIn("stress_evaluation", result)
        self.assertIn("rebalance_trigger", result)
        self.assertEqual(result["stress_evaluation"], expected_stress_result)
        self.assertEqual(result["rebalance_trigger"], expected_trigger_result)

        mock_evaluator_instance.evaluate_stress.assert_called_once_with(
            self.portfolio_id, self.prices, self.scenario_code, self.confidence_level
        )
        mock_trigger_instance.evaluate_and_trigger.assert_called_once_with(
            self.portfolio_id, self.threshold
        )

    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.MarketPortfolioMLStressEvaluator')
    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.StressAutoRebalanceTrigger')
    def test_evaluate_and_adapt_stress_evaluation_failure(self, mock_trigger_cls, mock_evaluator_cls) -> None:
        mock_evaluator_instance = mock_evaluator_cls.return_value
        error_message = uuid.uuid4().hex
        mock_evaluator_instance.evaluate_stress.side_effect = StressEvaluationError(error_message)

        allocator = MLStressAdaptiveAllocator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            window_size=self.window_size
        )

        with self.assertRaises(AdaptiveAllocationError) as ctx:
            allocator.evaluate_and_adapt(
                portfolio_id=self.portfolio_id,
                prices=self.prices,
                scenario_code=self.scenario_code,
                confidence_level=self.confidence_level,
                threshold=self.threshold
            )

        self.assertIn(error_message, str(ctx.exception))

    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.MarketPortfolioMLStressEvaluator')
    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.StressAutoRebalanceTrigger')
    def test_process_external_feed_and_allocate(self, mock_trigger_cls, mock_evaluator_cls) -> None:
        mock_trigger_instance = mock_trigger_cls.return_value
        random_bytes = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        mock_trigger_instance.fetch_external_stress_feed.return_value = random_bytes.getvalue()

        mock_evaluator_instance = mock_evaluator_cls.return_value
        parsed_stream_result = uuid.uuid4().hex
        mock_evaluator_instance.parse_external_stream.return_value = parsed_stream_result

        allocator = MLStressAdaptiveAllocator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            window_size=self.window_size
        )

        res = allocator.process_external_feed_and_allocate(
            target_url=self.source_url,
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code
        )

        self.assertEqual(res["parsed_stream"], parsed_stream_result)
        mock_trigger_instance.fetch_external_stress_feed.assert_called_once_with(self.source_url)
        mock_evaluator_instance.parse_external_stream.assert_called_once()

    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.MarketPortfolioMLStressEvaluator')
    @patch('skills.market_portfolio_ml_stress_adaptive_allocator.StressAutoRebalanceTrigger')
    def test_notify_audit_on_adaptive_action(self, mock_trigger_cls, mock_evaluator_cls) -> None:
        mock_trigger_instance = mock_trigger_cls.return_value
        alert_id = uuid.uuid4().hex
        audit_message = uuid.uuid4().hex
        audit_response = {"status": "LOGGED", "id": alert_id}
        mock_trigger_instance.notify_audit_system.return_value = audit_response

        allocator = MLStressAdaptiveAllocator(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            window_size=self.window_size
        )

        response = allocator.notify_allocation_audit(alert_id=alert_id, message=audit_message)

        self.assertEqual(response, audit_response)
        mock_trigger_instance.notify_audit_system.assert_called_once_with(alert_id, audit_message)


if __name__ == '__main__':
    unittest.main()