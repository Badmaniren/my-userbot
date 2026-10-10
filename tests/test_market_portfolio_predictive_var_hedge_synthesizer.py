import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine, VarEngineError, InsufficientDataError
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
import skills.market_portfolio_predictive_var_hedge_synthesizer as synthesizer


class TestMarketPortfolioPredictiveVarHedgeSynthesizer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = "".join(random.choices(string.ascii_uppercase, k=6))
        self.request_id = str(uuid.uuid4())
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.shifts = random.randint(1, 10)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.horizon_days = random.randint(1, 30)
        self.simulations = random.randint(100, 5000)
        self.iterations = random.randint(50, 1000)

    def test_synthesizer_initialization(self):
        rnd_db = str(uuid.uuid4())
        rnd_storage = f"/{str(uuid.uuid4())}/{str(uuid.uuid4())}.json"
        
        mock_db = MagicMock()
        mock_monitor = MagicMock()
        mock_evaluator = MagicMock()
        mock_rebalancer = MagicMock()
        mock_advisor = MagicMock()
        mock_pipeline = MagicMock()
        mock_anomaly_detector = MagicMock()
        mock_extractor = MagicMock()

        with patch("skills.market_portfolio_predictive_var_hedge_synthesizer.PredictiveVarEngine") as MockVarEngine, \
             patch("skills.market_portfolio_predictive_var_hedge_synthesizer.MarketPortfolioStressAutoHedgeSync") as MockHedgeSync:
            
            instance = synthesizer.PredictiveVarHedgeSynthesizer(
                db_storage=mock_db,
                extractor_tool=mock_extractor,
                market_anomaly_detector=mock_anomaly_detector,
                monitor=mock_monitor,
                evaluator=mock_evaluator,
                rebalancer=mock_rebalancer,
                storage_file=rnd_storage,
                advisor=mock_advisor,
                pipeline=mock_pipeline
            )

            MockVarEngine.assert_called_once_with(mock_db, mock_extractor, mock_anomaly_detector)
            MockHedgeSync.assert_called_once_with(mock_db, mock_monitor, mock_evaluator, mock_rebalancer, rnd_storage, mock_advisor, mock_pipeline)
            self.assertIsNotNone(instance)

    def test_synthesize_and_execute_hedge_success(self):
        mock_db = MagicMock()
        mock_extractor = MagicMock()
        mock_anomaly_detector = MagicMock()
        mock_monitor = MagicMock()
        mock_evaluator = MagicMock()
        mock_rebalancer = MagicMock()
        mock_advisor = MagicMock()
        mock_pipeline = MagicMock()

        expected_var_result = {
            "portfolio_id": self.portfolio_id,
            "predictive_var": round(random.uniform(1000.0, 50000.0), 2),
            "confidence": self.confidence_level
        }
        expected_hedge_result = {
            "status": "SYNCHRONIZED",
            "request_id": self.request_id,
            "symbol": self.symbol,
            "executed_percentage": self.percentage
        }

        with patch.object(PredictiveVarEngine, "calculate_predictive_var", return_value=expected_var_result) as mock_calc_var, \
             patch.object(MarketPortfolioStressAutoHedgeSync, "synchronize", return_value=expected_hedge_result) as mock_sync_hedge:

            synth = synthesizer.PredictiveVarHedgeSynthesizer(
                db_storage=mock_db,
                extractor_tool=mock_extractor,
                market_anomaly_detector=mock_anomaly_detector,
                monitor=mock_monitor,
                evaluator=mock_evaluator,
                rebalancer=mock_rebalancer,
                storage_file=str(uuid.uuid4()),
                advisor=mock_advisor,
                pipeline=mock_pipeline
            )

            scenario_params = {"param_key": str(uuid.uuid4())}
            result = synth.synthesize_and_execute_hedge(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                iterations=self.iterations,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_calc_var.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                iterations=self.iterations
            )

            mock_sync_hedge.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["var_metrics"], expected_var_result)
            self.assertEqual(result["hedge_result"], expected_hedge_result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)

    def test_synthesize_and_execute_hedge_var_error(self):
        mock_db = MagicMock()
        mock_extractor = MagicMock()
        mock_anomaly_detector = MagicMock()

        error_message = f"VarEngineFailed-{str(uuid.uuid4())}"

        with patch.object(PredictiveVarEngine, "calculate_predictive_var", side_effect=VarEngineError(error_message)) as mock_calc_var:

            synth = synthesizer.PredictiveVarHedgeSynthesizer(
                db_storage=mock_db,
                extractor_tool=mock_extractor,
                market_anomaly_detector=mock_anomaly_detector,
                monitor=MagicMock(),
                evaluator=MagicMock(),
                rebalancer=MagicMock(),
                storage_file=str(uuid.uuid4()),
                advisor=MagicMock(),
                pipeline=MagicMock()
            )

            with self.assertRaises(VarEngineError) as ctx:
                synth.synthesize_and_execute_hedge(
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days,
                    confidence_level=self.confidence_level,
                    portfolio_value=self.portfolio_value,
                    scenario_params={},
                    iterations=self.iterations,
                    request_id=self.request_id,
                    symbol=self.symbol,
                    percentage=self.percentage,
                    shifts=self.shifts
                )

            self.assertIn(error_message, str(ctx.exception))

    def test_synthesize_stress_var_and_hedge(self):
        mock_db = MagicMock()
        mock_extractor = MagicMock()
        mock_anomaly_detector = MagicMock()
        mock_monitor = MagicMock()
        mock_evaluator = MagicMock()
        mock_rebalancer = MagicMock()

        expected_stress_var = {
            "stress_var": round(random.uniform(5000.0, 100000.0), 2),
            "portfolio_id": self.portfolio_id
        }
        expected_hedge_res = {
            "status": "STRESS_SYNCHRONIZED",
            "request_id": self.request_id
        }

        with patch.object(PredictiveVarEngine, "calculate_predictive_stress_var", return_value=expected_stress_var) as mock_stress_var, \
             patch.object(MarketPortfolioStressAutoHedgeSync, "synchronize", return_value=expected_hedge_res) as mock_sync:

            synth = synthesizer.PredictiveVarHedgeSynthesizer(
                db_storage=mock_db,
                extractor_tool=mock_extractor,
                market_anomaly_detector=mock_anomaly_detector,
                monitor=mock_monitor,
                evaluator=mock_evaluator,
                rebalancer=mock_rebalancer,
                storage_file=str(uuid.uuid4()),
                advisor=MagicMock(),
                pipeline=MagicMock()
            )

            scenario_params = {"stress_factor": random.uniform(1.1, 3.5)}
            res = synth.synthesize_stress_var_and_hedge(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.iterations,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_stress_var.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                iterations=self.iterations
            )

            mock_sync.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res["stress_var_metrics"], expected_stress_var)
            self.assertEqual(res["hedge_result"], expected_hedge_res)

    def test_stream_processing_and_hedge_trigger(self):
        mock_db = MagicMock()
        mock_extractor = MagicMock()
        mock_anomaly_detector = MagicMock()

        random_stream_data = f"stream-payload-{uuid.uuid4()}".encode('utf-8')
        stream_mock = io.BytesIO(random_stream_data)

        expected_stream_response = {"status": "STREAM_PROCESSED", "bytes": len(random_stream_data)}
        expected_hedge_res = {"status": "STREAM_HEDGE_SYNC"}

        with patch.object(PredictiveVarEngine, "process_market_stream", return_value=expected_stream_response) as mock_process, \
             patch.object(MarketPortfolioStressAutoHedgeSync, "synchronize", return_value=expected_hedge_res) as mock_sync:

            synth = synthesizer.PredictiveVarHedgeSynthesizer(
                db_storage=mock_db,
                extractor_tool=mock_extractor,
                market_anomaly_detector=mock_anomaly_detector,
                monitor=MagicMock(),
                evaluator=MagicMock(),
                rebalancer=MagicMock(),
                storage_file=str(uuid.uuid4()),
                advisor=MagicMock(),
                pipeline=MagicMock()
            )

            res = synth.process_stream_and_auto_hedge(
                stream_mock=stream_mock,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_process.assert_called_once_with(stream_mock)
            mock_sync.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res["stream_response"], expected_stream_response)
            self.assertEqual(res["hedge_result"], expected_hedge_res)
            self.assertEqual(stream_mock.read(), random_stream_data)