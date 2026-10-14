import logging
import io

logger = logging.getLogger(__name__)

class LessonParserError(Exception):
    """Исключение, возникающее при ошибках парсинга уроков."""
    pass

class LessonParser:
    def __init__(self, git_inspector):
        self.git_inspector = git_inspector

    def parse_lessons(self):
        """Парсит историю репозитория и извлекает уроки (ошибки и победы)."""
        forbidden_chars = {'§', '©', '®', '™', 'ø'}
        lessons = []
        
        try:
            history = self.git_inspector.get_history()
            changes = self.git_inspector.get_latest_changes()
            
            if not history and not changes:
                return []

            for commit in history:
                if not isinstance(commit, dict) or 'hash' not in commit:
                    logger.warning("Некорректная структура коммита: %s", commit)
                    continue
                
                c_hash = commit.get('hash')
                msg = commit.get('message', '')
                
                # Читаем файл на момент коммита, если поддерживается
                try:
                    file_obj = self.git_inspector.read_file_at_commit(c_hash, "")
                    if file_obj:
                        content_bytes = file_obj.read()
                        
                        # Проверка на запрещенные символы
                        try:
                            content_str = content_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            content_str = content_bytes.decode('latin1', errors='ignore')
                            
                        for char in forbidden_chars:
                            if char in content_str:
                                raise LessonParserError(f"Найден запрещенный символ: {char}")
                                
                        lessons.append({
                            'commit': c_hash,
                            'description': msg,
                            'content': content_str
                        })
                except LessonParserError:
                    raise
                except Exception as read_err:
                    # Если файл не удалось прочитать, логируем предупреждение и используем сообщение коммита
                    logger.warning("Не удалось прочитать файл для коммита %s: %s", c_hash, read_err)
                    lessons.append({
                        'commit': c_hash,
                        'description': msg,
                        'content': msg
                    })

        except LessonParserError:
            raise
        except Exception as e:
            raise LessonParserError(str(e))
            
        return lessons

    def extract_lessons(self, max_commits=10):
        """Интеграционный метод для извлечения уроков с фильтрацией запрещенных слов."""
        forbidden_words = {"запрещено"}
        lessons = []
        
        try:
            history = self.git_inspector.get_history(max_count=max_commits)
            if history is None:
                return []
                
            for commit in history:
                if not isinstance(commit, dict):
                    continue
                c_hash = commit.get('hash')
                msg = commit.get('message', '')
                
                content = msg
                try:
                    file_obj = self.git_inspector.read_file_at_commit(c_hash, "")
                    if file_obj:
                        content = file_obj.read().decode('utf-8', errors='ignore')
                except Exception as file_err:
                    logger.debug("Не удалось прочитать файл в extract_lessons для коммита %s: %s", c_hash, file_err)

                # Фильтрация запрещенных слов
                skip = False
                for word in forbidden_words:
                    if word in content:
                        skip = True
                        break
                
                if skip:
                    continue

                lessons.append({
                    "commit": c_hash,
                    "content": content
                })
        except Exception as inspector_err:
            # Осмысленно логируем ошибку инспектора и возвращаем пустой список согласно интеграционному тесту
            logger.error("Ошибка при работе инспектора в extract_lessons: %s", inspector_err)
            return []
            
        return lessons