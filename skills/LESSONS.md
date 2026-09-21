# Уроки Унги

Это файл, который бот пишет и читает сам.

...(старые уроки обрезаны)...
LED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_database_pipeline (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_notifier (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## telegram_sender (create) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## price_alerter (create) — раундов: 4
- Античит поймал: Синтаксическая ошибка в коде: expected 'else' after 'if' expression (<unknown>, line 91); АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_database_notifier (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: return [line.decode('utf-8') for line in lines]
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_database_pipeline (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_notifier (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=2, errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_telegram_pipeline (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_alert_analyzer (compose) — раундов: 4
- Античит поймал: Синтаксическая ошибка в коде: invalid syntax (<unknown>, line 1)
- Последняя ошибка перед фиксом: FAILED (failures=2, errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_threshold_alerter (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_threshold_checker (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_alert_trigger (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1, errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_threshold_analyzer (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_report_generator (compose) — раундов: 3
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_export_pipeline (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_database_pipeline (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.; АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_status_analyzer (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_database_notifier (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_threshold_pipeline (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=3)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_telegram_pipeline (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_report_generator (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: успешно прошёл тесты и влит в main

## market_database_pipeline (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_parser (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_parser (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_telegram_pipeline (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## db_storage (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_parser (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## db_storage (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_report_generator (refactor) — раундов: 2
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: успешно прошёл тесты и влит в main

## market_report_generator (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_tracker (start_new) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.; АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: retries = retries.increment(
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_analytics (start_new) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: - []
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_monitor (start_new) — раундов: 3
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_valuation (compose) — раундов: 2
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_alert_dispatcher (compose) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_visualizer (create) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_visualizer_v2 (create) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_trend_analyzer (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_digest (compose) — раундов: 3
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_risk_calculator (create) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_backtester (create) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=3)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_optimizer (create) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.; АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_rebalancer (create) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_validator (create) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_scenario_simulator (create) — раундов: 3
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_stress_reporter (compose) — раундов: 4
- Последняя ошибка перед фиксом: Actual: not called.
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_stress_reporter (compose) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_collector_agent (start_new) — раундов: 2
- Последняя ошибка перед фиксом: FAILED (failures=2)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_predictive_analyzer (compose) — раундов: 4
- Античит поймал: Синтаксическая ошибка в коде: invalid syntax (<unknown>, line 1)
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_predictive_engine (compose) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.; АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1, errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_predictive_aggregator (compose) — раундов: 3
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_autonomous_sentinel (compose) — раундов: 3
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_audit_logger (start_new) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_performance_tracker (start_new) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.; АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: Expected: MarketParser('c853492b4d3549a98bf022d7e521ac48.json')
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_export (create) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_api_gateway (start_new) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_webhook_sync (compose) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=3)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_exporter (create) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_data_exporter (compose) — раундов: 2
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_integration_hub (compose) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_alert_dispatcher (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_integration_hub (compose) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_webhook_sync (start_new) — раундов: 2
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_webhook_sync (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_alert_dispatcher (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_webhook_event_logger (compose) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_webhook_sync (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_analytics_dashboard (start_new) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.; АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_websocket_bridge (start_new) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (errors=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_performance_analytics (start_new) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_performance_analytics (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_risk_engine (create) — раундов: 4
- Античит поймал: Синтаксическая ошибка в коде: invalid syntax (<unknown>, line 1); Синтаксическая ошибка в коде: invalid syntax (<unknown>, line 1); Синтаксическая ошибка в коде: invalid syntax (<unknown>, line 1)
- Последняя ошибка перед фиксом: FAILED (errors=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_advanced_metrics (create) — раундов: 4
- Античит поймал: АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! Обработай ошибку предсказуемо или пробрось наружу через raise.
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_performance_analytics (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_performance_analytics (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=2)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_performance_analytics (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_stress_reporter (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: ПРОВАЛЕН Унгой, передан на эскалацию

## market_portfolio_performance_analytics (refactor) — раундов: 1
- Статус: успешно прошёл тесты и влит в main

## market_portfolio_performance_analytics (refactor) — раундов: 4
- Последняя ошибка перед фиксом: FAILED (failures=1)
- Статус: успешно прошёл тесты и влит в main
