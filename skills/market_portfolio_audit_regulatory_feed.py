try:
    import requests
    import bs4
except ImportError:
    requests = None
    bs4 = None

from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub


def extract_stream_data(stream):
    return stream.read().decode('utf-8')


class RegulatoryFeedAggregator:
    def __init__(self, db_storage=None, extractor_tool=None, market_parser=None, audit_compliance_hub=None):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_parser = market_parser
        self.audit_compliance_hub = audit_compliance_hub

    def fetch_and_store_feed(self, url: str) -> bool:
        if requests is None:
            return False
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            if bs4 is not None:
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                rule_elem = soup.find('div', id='content')
                rule_text = rule_elem.text if rule_elem else response.text
            else:
                rule_text = response.text

            if self.db_storage:
                self.db_storage.save_regulation({"rule": rule_text, "source": url})
            return True
        except Exception:
            return False

    def parse_document_stream(self, stream, document_id: str) -> dict:
        data = extract_stream_data(stream)
        if self.extractor_tool:
            self.extractor_tool(data)
        return {
            "document_id": document_id,
            "data": data
        }

    def run_compliance_audit(self, portfolio_id: str) -> dict:
        regulations = []
        if self.db_storage and hasattr(self.db_storage, "get_active_regulations"):
            regulations = self.db_storage.get_active_regulations()

        if self.audit_compliance_hub and hasattr(self.audit_compliance_hub, "verify_rule"):
            for reg in regulations:
                self.audit_compliance_hub.verify_rule(portfolio_id, reg)

        return {
            "status": "COMPLETED",
            "portfolio_id": portfolio_id,
            "regulations_checked": len(regulations)
        }

    def handle_market_anomaly(self, payload: dict):
        self.dispatch_alert(payload)

    def dispatch_alert(self, payload: dict):
        pass


def market_portfolio_audit_regulatory_feed(compliance_result: dict) -> dict:
    return {
        "feed_id": compliance_result.get("feed_id"),
        "code": compliance_result.get("code"),
        "processed": True
    }
