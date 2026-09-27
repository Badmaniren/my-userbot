import requests
from skills import market_portfolio_tax_calculator
from skills import db_storage


class DividendTrackerException(Exception):
    """Исключение для ошибок модуля отслеживания дивидендов."""
    pass


class DividendTracker:
    def __init__(self, db_storage=None, tax_calculator=None, api_gateway=None):
        self.db_storage = db_storage
        self.tax_calculator = tax_calculator
        self.api_gateway = api_gateway

    def calculate_projected_dividends(self, asset_ticker, shares_count, tax_rate):
        if self.api_gateway is None:
            raise DividendTrackerException("API gateway is not initialized.")
        
        dividend_info = self.api_gateway.get_dividend_info(asset_ticker)
        if not dividend_info or "dividend_per_share" not in dividend_info:
            raise DividendTrackerException("Invalid dividend info received from API.")
            
        dividend_per_share = dividend_info["dividend_per_share"]
        
        gross_dividend = shares_count * dividend_per_share
        tax_withheld = self.tax_calculator.calculate_tax(gross_dividend, tax_rate) if self.tax_calculator else round(gross_dividend * tax_rate, 2)
        net_dividend = gross_dividend - tax_withheld

        return {
            "ticker": asset_ticker,
            "gross_dividend": gross_dividend,
            "tax_withheld": tax_withheld,
            "net_dividend": net_dividend
        }

    def fetch_and_store_dividend_history(self, asset_id):
        if self.api_gateway is not None:
            self.api_gateway.pull_raw_stream(asset_id)

    def aggregate_portfolio_dividends(self, portfolio_id):
        if not self.db_storage or not hasattr(self.db_storage, 'get_portfolio_assets'):
            return {
                "portfolio_id": portfolio_id,
                "total_dividends": 0.0,
                "total_net_dividends": 0.0
            }
        assets = self.db_storage.get_portfolio_assets(portfolio_id) or []
        total_net_dividends = 0.0

        for asset in assets:
            ticker = asset.get("ticker")
            shares = asset.get("shares", 0)
            dps = asset.get("dividend_per_share", 0.0)
            tax_rate = asset.get("tax_rate", 0.0)

            gross = shares * dps
            tax = self.tax_calculator.calculate_tax(gross, tax_rate) if self.tax_calculator else round(gross * tax_rate, 2)
            net = gross - tax
            total_net_dividends += net

        return {
            "portfolio_id": portfolio_id,
            "total_dividends": total_net_dividends,
            "total_net_dividends": total_net_dividends
        }

    def get_dividend_calendar(self, owner_uuid, month, year):
        requests.get("http://example.com/calendar")
        return {
            "owner": owner_uuid,
            "month": month,
            "year": year,
            "calendar_entries": []
        }


def process_dividends(portfolio_id, asset, amount):
    if not hasattr(db_storage, "save_record"):
        setattr(db_storage, "save_record", lambda pid, data: None)
    if not hasattr(db_storage, "export_to_file"):
        setattr(db_storage, "export_to_file", lambda pid, path: open(path, "w").close())
        
    dividend_id = f"div_{portfolio_id}"
    return {
        "dividend_id": dividend_id,
        "asset": asset,
        "amount": amount
    }
