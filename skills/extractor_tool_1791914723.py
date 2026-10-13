import xml.etree.ElementTree as ET
from skills import db_storage

def extract_metadata_from_markup(markup: str) -> dict:
    """
    Извлекает метаданные (id, value, session) из XML-разметки,
    сохраняет их в db_storage и возвращает результат.
    """
    try:
        # Парсинг XML-строки. 
        # Если markup=None, ET.fromstring вызовет TypeError.
        # Если markup - некорректная XML-строка, ET.fromstring вызовет ParseError.
        root = ET.fromstring(markup)
        
        # Поиск узлов через XPath (позволяет находить элементы на любой глубине)
        id_node = root.find(".//id")
        value_node = root.find(".//value")
        session_node = root.find(".//session")
        
        # Проверка наличия всех обязательных полей
        if id_node is None or value_node is None or session_node is None:
            return {
                "success": False,
                "error": "Required metadata fields (id, value, session) not found"
            }
        
        # Извлечение текстового содержимого узлов
        extracted_id = id_node.text
        extracted_value = value_node.text
        session_id = session_node.text
        
        # Сохранение данных в db_storage.
        # Мы импортируем db_storage как модуль, предполагая, что save_record — это функция внутри него.
        # Это исправляет ImportError, возникавший при попытке импортировать объект из модуля.
        db_storage.save_record(extracted_id, {
            "session_id": session_id,
            "extracted_value": extracted_value
        })
        
        # Возврат структуры, ожидаемой тестами
        return {
            "id": extracted_id,
            "value": extracted_value,
            "success": True
        }
        
    except (ET.ParseError, TypeError, AttributeError) as e:
        # Обработка ошибок парсинга и некорректных типов данных (например, None)
        return {
            "success": False,
            "error": f"Failed to parse markup: {str(e)}"
        }
    except Exception as e:
        # Общий перехват исключений для обработки ошибок БД и обеспечения устойчивости
        return {
            "success": False,
            "error": str(e)
        }