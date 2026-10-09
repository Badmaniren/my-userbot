from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class MarketPortfolioStressAutoHedgeSync:
    def __init__(
        self,
        db_storage=None,
        monitor=None,
        evaluator=None,
        rebalancer=None,
        storage_file=None,
        advisor=None,
        pipeline=None
    ):
        self.db_storage = db_storage
        self.monitor = monitor
        self.evaluator = evaluator
        self.rebalancer = rebalancer
        self.storage_file = storage_file
        
        self.advisor = advisor if advisor is not None else MarketPortfolioStressHedgeAdvisor(
            db_storage=self.db_storage,
            monitor=self.monitor,
            evaluator=self.evaluator,
            rebalancer=self.rebalancer
        )
        
        self.pipeline = pipeline if pipeline is not None else PortfolioStressScenarioPipeline(
            storage_file=self.storage_file
        )
        
        self.stream_handler = None

    def synchronize(
        self,
        portfolio_id,
        request_id,
        symbol,
        percentage,
        shifts
    ):
        advisor_recommendation = self.advisor.analyze_and_recommend(
            portfolio_id=portfolio_id,
            request_id=request_id
        )
        
        stress_pipeline_result = self.pipeline.execute(
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )
        
        result = {
            "status": "success",
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "advisor_recommendation": advisor_recommendation,
            "stress_pipeline_result": stress_pipeline_result
        }
        return result


def run_auto_hedge_sync(
    db_storage,
    monitor,
    evaluator,
    rebalancer,
    storage_file,
    portfolio_id,
    request_id,
    symbol,
    percentage,
    shifts
):
    syncer = MarketPortfolioStressAutoHedgeSync(
        db_storage=db_storage,
        monitor=monitor,
        evaluator=evaluator,
        rebalancer=rebalancer,
        storage_file=storage_file
    )
    return syncer.synchronize(
        portfolio_id=portfolio_id,
        request_id=request_id,
        symbol=symbol,
        percentage=percentage,
        shifts=shifts
    )