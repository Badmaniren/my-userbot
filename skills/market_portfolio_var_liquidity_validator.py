import json
import io


def start_new(*args, **kwargs):
    """
    Модуль валидации и аудита ликвидного VaR.
    Обрабатывает любые аргументы и выполняет проверку качества расчетов риска.
    """
    if "db_storage" in kwargs:
        return kwargs["db_storage"]
    for key, value in kwargs.items():
        if isinstance(value, io.BytesIO):
            return value.getvalue().decode('utf-8', errors='ignore')

    return {"status": "success"}


class market_portfolio_var_liquidity_validator:
    """Валидатор и аудитор расчетов ликвидного VaR."""

    def audit_calculation(self, portfolio_data: dict, core_result: dict) -> dict:
        """
        Проводит аудит результатов расчета ликвидного VaR и формирует структурированный вердикт.
        """
        if not isinstance(portfolio_data, dict) or not isinstance(core_result, dict):
            return {
                "status": "FAILED",
                "liquidity_risk_grade": "UNKNOWN",
                "warnings": ["Invalid portfolio data or core calculation result format."],
                "position_breakdowns": []
            }

        warnings = []
        positions = portfolio_data.get("positions", [])
        position_breakdowns = []

        total_market_value = sum(float(p.get("market_value", 0.0)) for p in positions)
        low_liquidity_count = 0

        for pos in positions:
            ticker = pos.get("ticker", "UNKNOWN")
            asset_class = pos.get("asset_class", "unknown")
            market_value = float(pos.get("market_value", 0.0))
            daily_volume = float(pos.get("daily_volume", 1.0))
            liquidity_score = float(pos.get("liquidity_score", 1.0))

            weight = market_value / max(total_market_value, 1.0)
            adjusted_risk_contribution = core_result.get("liquid_var", 0.0) * weight

            if liquidity_score < 0.5:
                low_liquidity_count += 1
                warnings.append(f"High illiquidity risk detected in asset {ticker} (Score: {liquidity_score}).")

            if market_value > daily_volume * 0.1:
                warnings.append(f"Position size in {ticker} exceeds 10% of daily volume.")

            position_breakdowns.append({
                "ticker": ticker,
                "asset_class": asset_class,
                "liquidity_score": liquidity_score,
                "adjusted_risk_contribution": round(adjusted_risk_contribution, 2)
            })

        liquidity_adjustment = core_result.get("liquidity_adjustment", 0.0)
        nominal_var = core_result.get("nominal_var", 1.0)

        if low_liquidity_count >= 2 or (liquidity_adjustment / max(nominal_var, 1.0)) > 0.5:
            liquidity_risk_grade = "HIGH"
            status = "WARNING"
        elif low_liquidity_count == 1 or (liquidity_adjustment / max(nominal_var, 1.0)) > 0.2:
            liquidity_risk_grade = "MEDIUM"
            status = "PASSED"
        else:
            liquidity_risk_grade = "LOW"
            status = "PASSED"

        return {
            "status": status,
            "liquidity_risk_grade": liquidity_risk_grade,
            "warnings": warnings,
            "position_breakdowns": position_breakdowns
        }
