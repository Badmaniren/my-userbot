import skills.market_portfolio_stress_hedge_advisor as market_portfolio_stress_hedge_advisor
import skills.market_portfolio_stress_scenario_pipeline as market_portfolio_stress_scenario_pipeline
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class DummyMonitor:
    def get_portfolio_state(self, portfolio_id):
        return {"portfolio_id": portfolio_id, "status": "active"}


class DummyRebalancer:
    def set_trigger_status(self, portfolio_id, status_data):
        return {"portfolio_id": portfolio_id, "status": "updated", "data": status_data}


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
        self.monitor = monitor if monitor is not None else DummyMonitor()
        self.evaluator = evaluator
        self.rebalancer = rebalancer if rebalancer is not None else DummyRebalancer()
        self.storage_file = storage_file
        
        if advisor is not None:
            self.advisor = advisor
        else:
            advisor_cls = getattr(
                market_portfolio_stress_hedge_advisor,
                "MarketPortfolioStressHedgeAdvisor",
                MarketPortfolioStressHedgeAdvisor
            )
            self.advisor = advisor_cls(
                db_storage=self.db_storage,
                monitor=self.monitor,
                evaluator=self.evaluator,
                rebalancer=self.rebalancer
            )
        
        if pipeline is not None:
            self.pipeline = pipeline
        else:
            pipeline_cls = getattr(
                market_portfolio_stress_scenario_pipeline,
                "PortfolioStressScenarioPipeline",
                PortfolioStressScenarioPipeline
            )
            self.pipeline = pipeline_cls(
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
        if getattr(self.advisor, 'monitor', None) is None:
            self.advisor.monitor = self.monitor

        if getattr(self.advisor, 'rebalancer', None) is None:
            self.advisor.rebalancer = self.rebalancer
        elif getattr(self.advisor.rebalancer, 'set_trigger_status', None) is None:
            self.advisor.rebalancer = self.rebalancer

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