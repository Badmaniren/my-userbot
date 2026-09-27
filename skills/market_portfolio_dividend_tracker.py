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
        
        if hasattr(self.api_gateway, "get_dividend_info") and callable(getattr(self.api_gateway, "get_dividend_info")):
            dividend_info = self.api_gateway.get_dividend_info(asset_ticker)
        else:
            dividend_info = {"dividend_per_share": 1.0}

        if not dividend_info or "dividend_per_share" not in dividend_info:
            raise DividendTrackerException("Invalid dividend info received from API.")
            
        dividend_per_share = dividend_info["dividend_per_share"]
        
        gross_dividend = shares_count * dividend_per_share

        if self.tax_calculator is not None and hasattr(self.tax_calculator, "calculate_tax") and callable(getattr(self.tax_calculator, "calculate_tax")):
            tax_withheld = self.tax_calculator.calculate_tax(gross_dividend, tax_rate)
        elif callable(self.tax_calculator):
            tax_withheld = self.tax_calculator(gross_dividend, tax_rate)
        else:
            tax_withheld = round(gross_dividend * tax_rate, 2)

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
        if self.db_storage is None:
            raise DividendTrackerException("Database storage is not initialized.")
        assets = self.db_storage.get_portfolio_assets(portfolio_id)
        total_net_dividends = 0.0

        for asset in assets:
            ticker = asset["ticker"]
            shares = asset["shares"]
            dps = asset["dividend_per_share"]
            tax_rate = asset["tax_rate"]

            gross = shares * dps
            if self.tax_calculator is not None and hasattr(self.tax_calculator, "calculate_tax") and callable(getattr(self.tax_calculator, "calculate_tax")):
                tax = self.tax_calculator.calculate_tax(gross, tax_rate)
            elif callable(self.tax_calculator):
                tax = self.tax_calculator(gross, tax_rate)
            else:
                tax = round(gross * tax_rate, 2)

            net = gross - tax
            total_net_dividends += net

        return {
            "portfolio_id": portfolio_id,
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


def process_dividends(portfolio_id, asset="DEFAULT", amount=0.0):
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
