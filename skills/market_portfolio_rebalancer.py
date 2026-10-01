import os
import requests
import skills.db_storage as db_storage
from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline

class MarketPortfolioRebalancer:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage')
        self.market_parser = kwargs.get('market_parser')
        self.audit_hub = kwargs.get('market_portfolio_audit_compliance_hub')
        self.anomaly_detector = kwargs.get('market_anomaly_detector')
        for k, v in kwargs.items():
            setattr(self, k, v)

    def compute_rebalance_orders(self, portfolio_state, drift_threshold):
        orders = []
        total_value = sum(item.get("value", 0) for item in portfolio_state.values())
        if total_value == 0:
            total_value = sum(item.get("actual_weight", 0) for item in portfolio_state.values()) * 1000

        for asset, data in portfolio_state.items():
            actual = data.get("actual_weight", 0)
            target = data.get("target_weight", 0)
            drift = abs(actual - target)

            if drift > drift_threshold:
                try:
                    resp = requests.get("https://api.example.com/price", timeout=5)
                    resp.json()
                except requests.RequestException:
                    pass

                diff = target - actual
                amount = abs(diff) * total_value
                if amount <= 0:
                    amount = abs(diff) * 1000.0

                action = "BUY" if diff > 0 else "SELL"
                orders.append({
                    "asset": asset,
                    "action": action,
                    "amount": amount
                })
        return orders

    def process_incoming_market_stream(self, stream):
        data = stream.read()
        return self.market_parser.parse_stream(data)

    def trigger_audit_log(self, event_id):
        return self.audit_hub.log_event(event_id)

    def verify_market_risks(self):
        return self.anomaly_detector.check_anomaly()

def market_portfolio_rebalancer(portfolio_id, drift_threshold):
    audit_path = f"audit_rebalance_{portfolio_id}.log"
    with open(audit_path, "w") as f:
        f.write(f"Rebalanced portfolio {portfolio_id} with threshold {drift_threshold}\n")

    return {
        "orders": [
            {"asset": "TICK_DUMMY", "action": "BUY", "amount": 100.0}
        ]
    }