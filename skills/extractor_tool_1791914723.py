import xml.etree.ElementTree as ET
from skills.db_storage import db_storage

def extract_metadata_from_markup(markup: str) -> dict:
    """
    Извлекает метаданные из XML-разметки и сохраняет их в db_storage.
    """
    try:
        # Парсинг XML
        root = ET.fromstring(markup)
        
        # Поиск необходимых полей через XPath
        id_node = root.find(".//id")
        value_node = root.find(".//value")
        session_node = root.find(".//session")
        
        # Проверка наличия обязательных узлов
        if id_node is None or value_node is None or session_node is None:
            return {
                "success": False,
                "error": "Required metadata fields (id, value, session) not found"
            }
        
        extracted_id = id_node.text
        extracted_value = value_node.text
        session_id = session_node.text
        
        # Интеграция с хранилищем: сохранение данных
        # Используем save_record, так как тест ожидает наличие данных через get_record
        db_storage.save_record(extracted_id, {
            "session_id": session_id,
            "extracted_value": extracted_value
        })
        
        return {
            "id": extracted_id,
            "value": extracted_value,
            "success": True
        }
        
    except (ET.ParseError, TypeError, AttributeError) as e:
        # Обработка некорректных данных или ошибок парсинга
        return {
            "success": False,
            "error": f"Failed to parse markup: {str(e)}"
        }
    except Exception as e:
        # Общий перехват для обеспечения устойчивости, требуемой тестами
        return {
            "success": False,
            "error": str(e)
        }