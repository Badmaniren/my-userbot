import io
import json
import os

from skills import market_portfolio_var_liquidity_core
from skills import market_portfolio_stress_scenario_pipeline


class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def execute(self, symbol, percentage, shifts):
        return market_portfolio_stress_scenario_pipeline.run_stress_scenario_pipeline(
            storage_file=self.storage_file,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )


class MarketPortfolioLiquidityStressEvaluator:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def evaluate_stress(
        self,
        portfolio_id,
        symbol,
        percentage,
        shifts,
        confidence_level=0.95,
        export_target=None
    ):
        try:
            var_func = getattr(market_portfolio_var_liquidity_core, "calculate_var_and_liquidity", None)
            if var_func is None and hasattr(market_portfolio_var_liquidity_core, "market_portfolio_var_liquidity_core"):
                core_inst = market_portfolio_var_liquidity_core.market_portfolio_var_liquidity_core()
                var_func = getattr(core_inst, "calculate_var_and_liquidity", None)

            var_result = var_func(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                export_target=export_target
            ) if var_func else {}

            pipeline = PortfolioStressScenarioPipeline(storage_file=self.storage_file)
            stress_result = pipeline.execute(
                symbol=symbol,
                percentage=percentage,
                shifts=shifts
            )

            var_loss = 0.0
            if isinstance(var_result, dict):
                var_loss = float(
                    var_result.get("var_value") or
                    var_result.get("var_loss") or
                    0.0
                )

            stress_loss = 0.0
            if isinstance(stress_result, dict):
                stress_loss = float(
                    stress_result.get("projected_loss") or
                    stress_result.get("scenario_loss") or
                    0.0
                )

            aggregate_loss = var_loss + stress_loss

            result = dict(var_result) if isinstance(var_result, dict) else {}
            if isinstance(stress_result, dict):
                result.update(stress_result)

            result["portfolio_id"] = portfolio_id
            result["aggregate_loss"] = aggregate_loss
            result["total_loss"] = aggregate_loss
            result["total_losses"] = aggregate_loss
            return result

        except Exception as e:
            return {"portfolio_id": portfolio_id, "error": str(e)}

    def execute(
        self,
        portfolio_id,
        symbol,
        percentage,
        shifts,
        confidence_level=0.95,
        export_target=None
    ):
        return self.evaluate_stress(
            portfolio_id=portfolio_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            confidence_level=confidence_level,
            export_target=export_target
        )

    def load_from_stream(self, stream: io.BytesIO):
        if stream:
            stream.seek(0, io.SEEK_END)


def evaluate_portfolio_liquidity_stress(
    portfolio_id,
    symbol,
    percentage,
    shifts,
    confidence_level=0.95,
    storage_file=None,
    export_target=None
):
    evaluator = MarketPortfolioLiquidityStressEvaluator(storage_file=storage_file)
    return evaluator.evaluate_stress(
        portfolio_id=portfolio_id,
        symbol=symbol,
        percentage=percentage,
        shifts=shifts,
        confidence_level=confidence_level,
        export_target=export_target
    )


def evaluate_liquidity_stress_losses(
    portfolio_id,
    symbol,
    confidence_level,
    percentage,
    shifts,
    export_target,
    storage_file
):
    res = evaluate_portfolio_liquidity_stress(
        portfolio_id=portfolio_id,
        symbol=symbol,
        percentage=percentage,
        shifts=shifts,
        confidence_level=confidence_level,
        storage_file=storage_file,
        export_target=export_target
    )
    if "total_losses" not in res:
        res["total_losses"] = res.get("aggregate_loss", 0.0)
    return res