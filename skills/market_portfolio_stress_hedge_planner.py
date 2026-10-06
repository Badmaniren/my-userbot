import skills.market_portfolio_stress_scenario_matrix_evaluator as scenario_matrix_evaluator
import skills.market_portfolio_execution_cost_optimizer as execution_cost_optimizer

# Re-exports for backward compatibility
MarketPortfolioStressScenarioMatrixEvaluator = scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator
evaluate_stress_scenario_matrix = scenario_matrix_evaluator.evaluate_stress_scenario_matrix
MarketPortfolioExecutionCostOptimizer = execution_cost_optimizer.MarketPortfolioExecutionCostOptimizer
market_portfolio_execution_cost_optimizer = execution_cost_optimizer.market_portfolio_execution_cost_optimizer

class MarketPortfolioStressHedgePlanner:
    def __init__(self, db_storage=None, extractor_tool_1790087207=None, extractor_tool_1790102839=None):
        try:
            self.evaluator = scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator(
                db_storage=db_storage,
                extractor_tool_1790087207=extractor_tool_1790087207,
                extractor_tool_1790102839=extractor_tool_1790102839
            )
        except Exception:
            try:
                self.evaluator = scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator()
            except Exception:
                self.evaluator = None

        try:
            self.optimizer = execution_cost_optimizer.MarketPortfolioExecutionCostOptimizer()
        except Exception:
            self.optimizer = None

    def execute_hedge_plan(self, portfolio_id, historical_window, asset, volume, ticker, slippage_model_output):
        try:
            stress_matrix = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
        except Exception:
            stress_matrix = {}

        try:
            execution_optimization = self.optimizer.optimize_execution_cost(
                portfolio_id=portfolio_id,
                asset=asset,
                volume=volume,
                ticker=ticker,
                slippage_model_output=slippage_model_output
            )
        except Exception:
            execution_optimization = {}

        return {
            "stress_matrix": stress_matrix,
            "execution_optimization": execution_optimization
        }

    def check_anomalies(self, scenario_token, threshold):
        try:
            return self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        except Exception:
            return False

    def evaluate_stream(self, portfolio_id, stream_data):
        try:
            return self.evaluator.evaluate_stream_matrix(portfolio_id, stream_data)
        except Exception:
            return {}

    def plan_hedge(self, *args, **kwargs):
        return plan_portfolio_stress_hedge(*args, **kwargs)


def plan_portfolio_hedge(payload):
    if not isinstance(payload, dict):
        payload = {}
    portfolio_id = payload.get("portfolio_id")
    historical_window = payload.get("historical_window")
    ticker = payload.get("ticker")
    volume = payload.get("volume")
    slippage = payload.get("slippage_model_output")

    try:
        matrix_result = scenario_matrix_evaluator.evaluate_stress_scenario_matrix(payload)
    except Exception:
        matrix_result = {}

    try:
        cost_opt_result = execution_cost_optimizer.market_portfolio_execution_cost_optimizer(
            portfolio_id=portfolio_id,
            ticker=ticker,
            volume=volume,
            slippage_model_output=slippage
        )
    except Exception:
        cost_opt_result = {}

    return {
        "matrix_evaluation": matrix_result,
        "cost_optimization": cost_opt_result
    }


def plan_portfolio_stress_hedge(portfolio_id, ticker, volume, historical_window, slippage_model_output):
    try:
        evaluator = scenario_matrix_evaluator.MarketPortfolioStressScenarioMatrixEvaluator()
        matrix_res = evaluator.evaluate_matrix(portfolio_id=portfolio_id, historical_window=historical_window)
    except Exception:
        matrix_res = {}

    try:
        optimizer = execution_cost_optimizer.MarketPortfolioExecutionCostOptimizer()
        opt_res = optimizer.optimize_execution_cost(
            portfolio_id=portfolio_id,
            asset=ticker,
            volume=volume,
            ticker=ticker,
            slippage_model_output=slippage_model_output
        )
    except Exception:
        opt_res = {}

    return {
        "hedge_orders": [opt_res],
        "total_estimated_cost": opt_res.get("optimized_cost", 0.0) if isinstance(opt_res, dict) else 0.0,
        "matrix_data": matrix_res
    }