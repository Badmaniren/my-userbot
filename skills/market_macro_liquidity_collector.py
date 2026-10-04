import sys
try:
    import requests
except ImportError:
    requests = None

from skills.db_storage import DbStorage as db_storage
from skills.db_storage import DBStorage, save_record, get_record
from skills.market_parser import market_parser, MarketParser


class market_macro_liquidity_collector:
    def __init__(self, db=None, parser=None):
        if db is not None:
            self.db = db
        else:
            self.db = db_storage() if callable(db_storage) else db_storage

        if parser is not None:
            self.parser = parser
        else:
            self.parser = market_parser() if callable(market_parser) else market_parser

    def collect(self, parsed_data):
        if not isinstance(parsed_data, dict):
            parsed_data = {}

        run_id = parsed_data.get("run_id")
        liquidity_index = parsed_data.get("liquidity_index")

        record = {
            "run_id": run_id,
            "liquidity_index": liquidity_index,
            **parsed_data
        }

        if hasattr(self.db, "save_record"):
            self.db.save_record(record, key=run_id)
        elif callable(save_record):
            save_record(record, key=run_id)

        return {
            "status": "success",
            "run_id": run_id,
            "collected": parsed_data
        }


def start_new(**kwargs):
    market_parser_tool = kwargs.get('market_parser')
    collector_agent = kwargs.get('market_portfolio_collector_agent')
    db_storage_tool = kwargs.get('db_storage')

    try:
        if hasattr(sys.stdin, 'read'):
            raw_input = sys.stdin.read()
            if isinstance(raw_input, bytes):
                try:
                    raw_input = raw_input.decode('utf-8', errors='ignore')
                except Exception:
                    raw_input = ""
    except Exception:
        raw_input = ""

    http_status = 200
    if requests is not None:
        try:
            response = requests.get('https://example.com/macro-liquidity', timeout=5)
            if hasattr(response, 'status_code'):
                http_status = response.status_code
        except Exception:
            http_status = 500

    parsed_result = None
    if market_parser_tool is not None:
        if hasattr(market_parser_tool, 'parse'):
            parsed_result = market_parser_tool.parse({})
        elif callable(market_parser_tool):
            parsed_result = market_parser_tool({})

    collected_result = None
    if collector_agent is not None:
        if hasattr(collector_agent, 'collect'):
            collected_result = collector_agent.collect(parsed_result)
        elif callable(collector_agent):
            collected_result = collector_agent(parsed_result)

    return {
        "parsed": parsed_result,
        "collected": collected_result,
        "http_status": http_status
    }
