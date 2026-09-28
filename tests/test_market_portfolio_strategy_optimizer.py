import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer

class TestPortfolioStrategyOptimizer(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        with patch('skills.market_portfolio_strategy_optimizer.MarketPortfolioBacktester'), \
             patch('skills.market_portfolio_strategy_optimizer.PortfolioScenarioSimulator'):
            self.optimizer = PortfolioStrategyOptimizer(self.storage_file)

    def test_init_and_storage(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        summary = self.optimizer.get_strategy_summary(rand_symbol)
        self.assertIn(rand_symbol, summary)
        self.assertEqual(summary[rand_symbol]["storage"], self.storage_file)
        self.assertEqual(summary[rand_symbol]["summary"], "active")

    def test_validate_allocation_boundaries_and_types(self):
        valid_val = round(random.uniform(0.0, 1.0), 4)
        self.assertEqual(self.optimizer._validate_allocation(valid_val), valid_val)

        over_val = 1.0 + random.uniform(0.1, 10.0)
        self.assertEqual(self.optimizer._validate_allocation(over_val), 1.0)

        under_val = -1.0 * random.uniform(0.1, 10.0)
        self.assertEqual(self.optimizer._validate_allocation(under_val), 0.0)

        str_val = str(random.choice([0.25, 0.5, 0.75]))
        self.assertEqual(self.optimizer._validate_allocation(str_val), float(str_val))

        invalid_str = f"corrupt_{uuid.uuid4().hex}"
        self.assertEqual(self.optimizer._validate_allocation(invalid_str), 0.0)
        self.assertEqual(self.optimizer._validate_allocation(None), 0.0)

    def test_optimize_strategy_success(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        rand_shift = random.randint(1, 100)
        rand_percentage = random.uniform(0.0, 100.0)
        
        mock_backtest_data = {uuid.uuid4().hex: random.random()}
        mock_simulation_data = {uuid.uuid4().hex: random.random()}

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=mock_backtest_data) as mock_bt, \
             patch.object(self.optimizer.simulator, 'simulate_scenario', return_value=mock_simulation_data) as mock_sim:
            
            result = self.optimizer.optimize_strategy(rand_symbol, rand_shift, rand_percentage)
            
            mock_bt.assert_called_once_with(rand_symbol, [rand_shift])
            mock_sim.assert_called_once_with(rand_symbol, rand_percentage)
            self.assertEqual(result['backtest'], mock_backtest_data)
            self.assertEqual(result['simulation'], mock_simulation_data)

    def test_optimize_strategy_key_error_handling(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        rand_shift = [random.randint(1, 50), random.randint(51, 100)]
        rand_percentage = random.uniform(0.0, 100.0)

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError), \
             patch.object(self.optimizer.simulator, 'simulate_scenario', side_effect=KeyError):
            
            result = self.optimizer.optimize_strategy(rand_symbol, rand_shift, rand_percentage)
            self.assertEqual(result['backtest'], {})
            self.assertEqual(result['simulation'], {})

    def test_evaluate_resilience_flow(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        rand_shift = random.randint(1, 10)
        rand_stress_key = uuid.uuid4().hex
        rand_stress_val = random.random()
        mock_stress_data = {rand_stress_key: rand_stress_val}
        
        drawdown_val = round(-random.uniform(0.1, 0.9), 2)

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value=mock_stress_data) as mock_stress, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val) as mock_dd:
            
            res = self.optimizer.evaluate_resilience(rand_symbol, rand_shift)
            
            mock_stress.assert_called_once_with(rand_symbol, [rand_shift])
            mock_dd.assert_called_once_with(rand_symbol)
            self.assertEqual(res['stress_data'], mock_stress_data)
            self.assertEqual(res['drawdown_checked'], drawdown_val)

    def test_evaluate_resilience_string_drawdown_and_exceptions(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        rand_shift = [random.randint(1, 10)]
        string_drawdown = str(round(-random.uniform(0.01, 0.5), 2))

        with patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=string_drawdown):
            
            res = self.optimizer.evaluate_resilience(rand_symbol, rand_shift)
            self.assertEqual(res['stress_data'], {})
            self.assertEqual(res['drawdown_checked'], float(string_drawdown))

        with patch.object(self.optimizer.simulator, 'run_stress_test', return_value={}), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=Exception("Critical Failure")):
            
            res = self.optimizer.evaluate_resilience(rand_symbol, rand_shift)
            self.assertEqual(res['drawdown_checked'], 0.0)

    def test_load_strategy_stream(self):
        rand_filepath = f"path/to/strategy_{uuid.uuid4().hex}.bin"
        rand_bytes = uuid.uuid4().bytes + random.randbytes(16)
        mock_file = io.BytesIO(rand_bytes)

        with patch("builtins.open", return_value=mock_file) as mock_open:
            data = self.optimizer.load_strategy_stream(rand_filepath)
            mock_open.assert_called_once_with(rand_filepath, 'rb')
            self.assertEqual(data, rand_bytes)

    def test_optimize_and_evaluate_comprehensive(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        raw_allocation = random.uniform(0.0, 1.0)
        rand_shift = random.randint(5, 50)
        
        bt_res_key = uuid.uuid4().hex
        stress_res_key = uuid.uuid4().hex
        mock_bt_res = {bt_res_key: random.random()}
        mock_stress_res = {stress_res_key: random.random()}
        drawdown_val = -0.35

        with patch.object(self.optimizer.backtester, 'run_backtest', return_value=mock_bt_res) as mock_bt, \
             patch.object(self.simulator if hasattr(self.optimizer, 'simulator') else self.optimizer.simulator, 'run_stress_test', return_value=mock_stress_res) as mock_st, \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', return_value=drawdown_val):
            
            result = self.optimizer.optimize_and_evaluate(rand_symbol, raw_allocation, rand_shift)
            
            mock_bt.assert_called_once_with(rand_symbol, [rand_shift])
            mock_st.assert_called_once_with(rand_symbol, [rand_shift])
            
            self.assertEqual(result["optimized_weights"], {rand_symbol: raw_allocation})
            self.assertAlmostEqual(result["resilience_score"], 1.0 - abs(drawdown_val))
            self.assertEqual(result["backtest"], mock_bt_res)
            self.assertEqual(result["stress"], mock_stress_res)

    def test_optimize_and_evaluate_fallback_resilience(self):
        rand_symbol = f"TICKER_{uuid.uuid4().hex[:5]}"
        allocation_out_of_bounds = 5.0
        rand_shifts = [random.randint(1, 10), random.randint(11, 20)]

        with patch.object(self.optimizer.backtester, 'run_backtest', side_effect=KeyError), \
             patch.object(self.optimizer.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(self.optimizer.backtester, 'calculate_maximum_drawdown', side_effect=TypeError):
            
            result = self.optimizer.optimize_and_evaluate(rand_symbol, allocation_out_of_bounds, rand_shifts)
            
            self.assertEqual(result["optimized_weights"], {rand_symbol: 1.0})
            self.assertEqual(result["resilience_score"], 0.5)
            self.assertEqual(result["backtest"], {})
            self.assertEqual(result["stress"], {})

if __name__ == '__main__':
    unittest.main()