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
        if not isinstance(shifts, (list, tuple)):
            return {
                "status": "error",
                "portfolio_id": portfolio_id,
                "request_id": request_id,
                "error": "Invalid shifts format: must be a list or tuple"
            }

        if not isinstance(percentage, (int, float)) or percentage <= 0 or percentage > 100:
            return {
                "status": "error",
                "portfolio_id": portfolio_id,
                "request_id": request_id,
                "error": "Invalid percentage: must be between 0 and 100"
            }

        if getattr(self.advisor, 'monitor', None) is None:
            self.advisor.monitor = self.monitor

        if getattr(self.advisor, 'rebalancer', None) is None:
            self.advisor.rebalancer = self.rebalancer
        elif getattr(self.advisor.rebalancer, 'set_trigger_status', None) is None:
            self.advisor.rebalancer = self.rebalancer

        try:
            advisor_recommendation = self.advisor.analyze_and_recommend(
                portfolio_id=portfolio_id,
                request_id=request_id
            )
        except Exception as e:
            return {
                "status": "error",
                "portfolio_id": portfolio_id,
                "request_id": request_id,
                "error": str(e)
            }
        
        if isinstance(advisor_recommendation, dict) and "portfolio_id" not in advisor_recommendation:
            advisor_recommendation["portfolio_id"] = portfolio_id
        
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