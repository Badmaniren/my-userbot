import io
import uuid
try:
    import requests
except ImportError:
    requests = None

from skills.db_storage import DBStorage
from skills.market_portfolio_var_liquidity_core import LiquidityCore
from skills.market_portfolio_stress_scenario_pipeline import StressScenarioPipeline


class MacroLiquidityTrackerConfig:
    def __init__(self, tracking_id, interest_rate, market_volume, enable_persistence=True):
        self.tracking_id = tracking_id
        self.interest_rate = interest_rate
        self.market_volume = market_volume
        self.enable_persistence = enable_persistence


def start_new(db_storage=None, **kwargs):
    extractor_tool_1 = kwargs.get('extractor_tool_1790087207')
    market_parser = kwargs.get('market_parser')

    data = {}
    if extractor_tool_1 and hasattr(extractor_tool_1, 'fetch_macro_data'):
        data = extractor_tool_1.fetch_macro_data()

    if market_parser and hasattr(market_parser, 'parse_stream'):
        stream = None
        if requests is not None:
            try:
                resp = requests.get("http://localhost", timeout=1)
                stream = io.BytesIO(resp.content)
            except Exception:
                stream = io.BytesIO(b"")
        else:
            stream = io.BytesIO(b"")
        market_parser.parse_stream(stream)

    if db_storage and hasattr(db_storage, 'save'):
        db_storage.save(data)

    return {"status": "success", "id": str(uuid.uuid4()), "data": data}


def track_macro_liquidity(config, db_storage=None, liquidity_core=None, stress_pipeline=None):
    result = {
        "tracking_id": config.tracking_id,
        "interest_rate": config.interest_rate,
        "market_volume": config.market_volume
    }

    if getattr(config, 'enable_persistence', True) and db_storage:
        if hasattr(db_storage, 'save_macro_liquidity'):
            db_storage.save_macro_liquidity(result)
        elif hasattr(db_storage, 'save'):
            db_storage.save(result)

    if liquidity_core:
        if hasattr(liquidity_core, 'compute_metrics'):
            liquidity_core.compute_metrics(config.tracking_id, result)

    if stress_pipeline and hasattr(stress_pipeline, 'run'):
        stress_pipeline.run(config.tracking_id)

    return result
