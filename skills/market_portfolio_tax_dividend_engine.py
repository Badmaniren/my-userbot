import uuid
import requests
from uuid import uuid4

from skills.market_portfolio_dividend_tracker import market_portfolio_dividend_tracker
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub
from skills.db_storage import db_storage

class MarketPortfolioTaxDividendEngine:
    def __init__(self, db_storage=None, market_portfolio_dividend_tracker=None,
                 market_portfolio_tax_calculator=None, market_portfolio_integration_hub=None):
        self.db_storage = db_storage if db_storage is not None else globals().get('db_storage')
        self.dividend_tracker = market_portfolio_dividend_tracker if market_portfolio_dividend_tracker is not None else globals().get('market_portfolio_dividend_tracker')
        self.tax_calculator = market_portfolio_tax_calculator if market_portfolio_tax_calculator is not None else globals().get('market_portfolio_tax_calculator')
        self.integration_hub = market_portfolio_integration_hub if market_portfolio_integration_hub is not None else globals().get('market_portfolio_integration_hub')

    def aggregate_tax_and_dividends(self, portfolio_id=None, user_id=None, db_conn_string=None):
        tracker = self.dividend_tracker if self.dividend_tracker is not None else market_portfolio_dividend_tracker
        calculator = self.tax_calculator if self.tax_calculator is not None else market_portfolio_tax_calculator
        storage = self.db_storage if self.db_storage is not None else db_storage

        if db_conn_string is not None:
            div_data = tracker.get_portfolio_dividends(portfolio_id)
            total_divs = div_data.get("total_dividends", 0.0)

            tax_data = calculator.get_calculated_tax(portfolio_id)
            total_tax = tax_data.get("total_tax", 0.0)

            return {
                "portfolio_id": portfolio_id,
                "total_dividends": total_divs,
                "total_tax": total_tax
            }

        div_result = tracker.fetch_portfolio_dividends(portfolio_id)
        tax_result = calculator.calculate_liability(portfolio_id)

        total_dividends = div_result["total_dividends"]
        total_tax_due = tax_result["total_tax_due"]
        net_income = round(total_dividends - total_tax_due, 2)

        response = {
            "portfolio_id": portfolio_id,
            "dividends": div_result,
            "taxes": tax_result,
            "net_income": net_income
        }

        if storage and hasattr(storage, "save_aggregation_audit"):
            storage.save_aggregation_audit(response)

        return response

    def verify_consistency(self, portfolio_id):
        tracker = self.dividend_tracker if self.dividend_tracker is not None else market_portfolio_dividend_tracker
        calculator = self.tax_calculator if self.tax_calculator is not None else market_portfolio_tax_calculator

        tracker_basis = tracker.get_tax_basis_sum(portfolio_id)
        calculator_basis = calculator.get_declared_basis_sum(portfolio_id)

        is_consistent = (tracker_basis == calculator_basis)
        discrepancy = round(abs(tracker_basis - calculator_basis), 2)
        incident_id = str(uuid4())

        return {
            "is_consistent": is_consistent,
            "tracker_basis": tracker_basis,
            "calculator_basis": calculator_basis,
            "discrepancy": discrepancy,
            "incident_id": incident_id
        }

    def export_audit_stream(self, destination_endpoint):
        storage = self.db_storage if self.db_storage is not None else db_storage
        stream_data = storage.get_audit_log_stream()
        data_bytes = stream_data.read()

        response = requests.post(destination_endpoint, data=data_bytes)
        return response.status_code in [200, 201, 204]

    def process_market_anomaly_event(self, anomaly_payload):
        calculator = self.tax_calculator if self.tax_calculator is not None else market_portfolio_tax_calculator
        hub = self.integration_hub if self.integration_hub is not None else market_portfolio_integration_hub

        ticker = anomaly_payload["ticker"]
        impact_multiplier = anomaly_payload["impact_multiplier"]
        anomaly_id = anomaly_payload["anomaly_id"]

        calculator.apply_multiplier(ticker, impact_multiplier)

        if hub and hasattr(hub, "broadcast_event"):
            hub.broadcast_event(anomaly_payload)

        return {
            "status": "success",
            "anomaly_id": anomaly_id
        }

market_portfolio_tax_dividend_engine = MarketPortfolioTaxDividendEngine()
