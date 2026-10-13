from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault


class MarketPortfolioStressAuditHealthMonitor:
    """
    Монитор здоровья аудита рыночного портфеля.
    Обеспечивает проверку целостности данных и анализ рисков на основе данных из Vault.
    """

    def __init__(self):
        self.vault = market_portfolio_stress_audit_summary_vault()

    def check_audit_integrity(self, audit_id: str) -> dict:
        """
        Проверяет целостность и состояние конкретного аудита.
        Интегрируется напрямую с market_portfolio_stress_audit_summary_vault.
        """
        # Получаем данные напрямую из хранилища
        audit_data = self.vault.get_audit_summary(audit_id)

        if not audit_data:
            return {
                "audit_id": audit_id,
                "status": "NOT_FOUND",
                "is_healthy": False,
                "health_level": "UNKNOWN"
            }

        # Извлекаем индекс риска (поддерживаем как risk_index, так и val для тестов агрегации)
        risk_index = audit_data.get("risk_index")
        if risk_index is None:
            risk_index = audit_data.get("val", 0.0)

        # Логика определения уровня здоровья
        if risk_index > 0.8:
            health_level = "CRITICAL"
        elif risk_index > 0.5:
            health_level = "WARNING"
        else:
            health_level = "STABLE"

        return {
            "audit_id": audit_id,
            "status": "OK",
            "is_healthy": True,
            "observed_risk": risk_index,
            "health_level": health_level,
            "timestamp": audit_data.get("timestamp"),
            "integrity_hash": audit_data.get("integrity_hash")
        }

    def generate_aggregate_health_report(self, audit_ids: list) -> dict:
        """
        Генерирует агрегированный отчет по списку идентификаторов аудитов.
        """
        report_map = {}
        processed_items = []

        for aid in audit_ids:
            status = self.check_audit_integrity(aid)
            report_map[aid] = status
            processed_items.append(aid)

        return {
            "processed_items": processed_items,
            "report_map": report_map,
            "total_count": len(processed_items)
        }


market_portfolio_stress_audit_health_monitor = MarketPortfolioStressAuditHealthMonitor
