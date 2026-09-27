import json
import os
import requests


class MarketPortfolioFundamentalScreener:
    def __init__(self, **kwargs):
        self.dependencies = kwargs

    def evaluate_and_filter(self, ticker: str, max_pe: float = 100.0, max_de: float = 10.0):
        url = f"https://api.example.com/financials/{ticker}"
        response = requests.get(url)
        content = response.content.decode('utf-8')

        data = {}
        for part in content.split(','):
            if ':' in part:
                k, v = part.split(':', 1)
                try:
                    data[k.strip()] = float(v.strip())
                except ValueError:
                    data[k.strip()] = v.strip()

        t = data.get('ticker', ticker)
        pe = data.get('pe', 10.0)
        pb = data.get('pb', 1.0)
        ps = data.get('ps', 1.0)
        de = data.get('de', 0.5)

        passed = (pe <= max_pe) and (de <= max_de)

        item = {
            'ticker': t,
            'pe': pe,
            'pb': pb,
            'ps': ps,
            'de': de,
            'passed': passed
        }

        if not passed:
            return []

        return [item]


def market_portfolio_fundamental_screener(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id", "default")
    assets = payload.get("assets", [])
    criteria = payload.get("criteria", {})

    max_pe = criteria.get("max_pe", 30.0)
    max_pb = criteria.get("max_pb", 5.0)
    max_de = criteria.get("max_debt_to_equity", 2.0)

    filtered_assets = []
    multipliers = {}

    for asset in assets:
        ticker = asset.get("ticker")
        price = asset.get("price", 0.0)
        eps = asset.get("eps", 1.0)
        bvps = asset.get("book_value_per_share", 1.0)
        sps = asset.get("sales_per_share", 1.0)
        de = asset.get("debt_to_equity", 0.0)

        pe = price / eps if eps else 0.0
        pb = price / bvps if bvps else 0.0
        ps = price / sps if sps else 0.0

        multipliers[ticker] = {
            "pe": pe,
            "pb": pb,
            "ps": ps,
            "debt_to_equity": de
        }

        if pe <= max_pe and pb <= max_pb and de <= max_de:
            filtered_assets.append(asset)

    os.makedirs("data_reports", exist_ok=True)
    output_filepath = f"data_reports/fundamental_screen_{portfolio_id}.json"

    report_data = {
        "portfolio_id": portfolio_id,
        "filtered_assets": filtered_assets,
        "multipliers": multipliers
    }

    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(report_data, f)

    from skills.db_storage import db_storage
    db_storage("set", portfolio_id, report_data)

    report_data["report_path"] = output_filepath
    return report_data