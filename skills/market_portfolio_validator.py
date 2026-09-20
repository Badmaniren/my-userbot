import json
import os

class MarketDataValidationError(Exception):
    """Вызывается при неверных рыночных данных."""
    pass

class PortfolioStructureValidationError(Exception):
    """Вызывается при неверной структуре портфеля."""
    pass


def load_stream_data():
    """Заглушка для загрузки стриминговых данных (патчится в тестах)."""
    return {}


def validate_market_data(raw_data):
    if not isinstance(raw_data, dict):
        raise MarketDataValidationError("Market data must be a dictionary")

    if "symbol" not in raw_data or "price" not in raw_data:
        raise MarketDataValidationError("Missing required fields: symbol, price")

    symbol = raw_data["symbol"]
    if not isinstance(symbol, str) or not symbol.strip():
        raise MarketDataValidationError("Symbol must be a non-empty string")

    price = raw_data["price"]
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        raise MarketDataValidationError("Price must be a number")

    if price < 0:
        raise MarketDataValidationError("Price cannot be negative")

    return raw_data


def validate_portfolio_structure(portfolio):
    if not isinstance(portfolio, dict):
        raise PortfolioStructureValidationError("Portfolio must be a dictionary")

    if "portfolio_id" not in portfolio:
        raise PortfolioStructureValidationError("Missing portfolio_id")

    if "assets" not in portfolio:
        raise PortfolioStructureValidationError("Missing assets in portfolio")

    assets = portfolio["assets"]
    if not isinstance(assets, list):
        raise PortfolioStructureValidationError("Assets must be a list")

    for asset in assets:
        if not isinstance(asset, dict):
            raise PortfolioStructureValidationError("Asset item must be a dictionary")

    return portfolio


def validate_market_portfolio_data(raw_data):
    """Функция интеграционной валидации, возвращающая булево значение."""
    try:
        if not isinstance(raw_data, dict) or not raw_data:
            return False
        for symbol, data in raw_data.items():
            if isinstance(data, dict):
                validate_market_data(data)
            else:
                return False
        return True
    except (MarketDataValidationError, PortfolioStructureValidationError, Exception):
        return False
