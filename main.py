import os
import sys
import time
import base64
import re
import json
import ast
import io
import zipfile
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. FAIL-FAST ПРОВЕРКА ОКРУЖЕНИЯ
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

if not GITHUB_TOKEN or not GITHUB_REPO or not API_KEYS:
    print("[FATAL] Отсутствуют критические переменные окружения (GITHUB_TOKEN, GITHUB_REPO, GEMINI_API_KEY)!")
    sys.exit(1)

# 2. СЕРВЕР ЖИЗНИ ДЛЯ RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pithecanthropus Hardened Daemon is operational.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 3. СЕТЬ И ОПТИМИЗИРОВАННЫЙ КЛИЕНТ GEMINI
def clean_url(url: str) -> str:
    return re.sub(r'\[.*?\]\(|\)', '', url).strip()

API_HOST = "generativelanguage.googleapis.com"
API_BASE = "https://" + API_HOST + "/v1beta/"
GITHUB_HOST = "api.github.com"
GITHUB_BASE = "https://" + GITHUB_HOST + "/repos/"

KEY_INDEX = 0
MODELS_CACHE = {"models": [], "expires_at": 0, "key": ""}

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_current_key():
    global KEY_INDEX
    return API_KEYS[KEY_INDEX % len(API_KEYS)]

def rotate_key():
    global KEY_INDEX, MODELS_CACHE
    if len(API_KEYS) > 1:
        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        MODELS_CACHE["expires_at"] = 0
        print(f"[!] Ротация ключа Gemini -> #{KEY_INDEX}")

def get_viable_models(key: str) -> list:
    global MODELS_CACHE
    now = time.time()
    if MODELS_CACHE["key"] == key and MODELS_CACHE["expires_at"] > now and MODELS_CACHE["models"]:
        return MODELS_CACHE["models"]

    url = clean_url(f"{API_BASE}models?key={key}")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = r.json().get("models", [])
            available = [m["name"] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
            flash_models = [m for m in available if "flash" in m.lower() and "preview" not in m.lower()]
            candidates = flash_models + [m for m in available if m not in flash_models]
            viable = []
            for m in candidates:
                test_url = clean_url(f"{API_BASE}{m}:generateContent?key={key}")
                try:
                    res = requests.post(test_url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=8)
                    if res.status_code == 200:
                        viable.append(m)
                        if len(viable) >= 2:
                            break
                except Exception:
                    continue
            if viable:
                MODELS_CACHE = {"models": viable, "expires_at": now + 3600, "key": key}
                return viable
    except Exception:
        pass
    return []

def strip_markdown(text: str) -> str:
    cleaned = re.sub(r'^```[a-zA-Z]*\n', '', text.strip(), flags=re.MULTILINE)
    return re.sub(r'```$', '', cleaned.strip(), flags=re.MULTILINE).strip()

def ask_gemini(prompt: str, json_mode: bool = False) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json" if json_mode else "text/plain"
        }
    }
    for _ in range(4):
        key = get_current_key()
        models = get_viable_models(key)
        if not models:
            rotate_key()
            time.sleep(2)
            continue
        for model in models:
            url = clean_url(f"{API_BASE}{model}:generateContent?key={key}")
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if r.status_code == 200:
                    ans = r.json()['candidates'][0]['content']['parts'][0]['text']
                    return strip_markdown(ans)
                if r.status_code in [429, 503]:
                    rotate_key()
                    time.sleep(2)
            except Exception:
                time.sleep(2)
    return ""

# 4. РАБОТА С GITHUB И ВЕТКАМИ
def get_main_sha() -> str:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    return r.json()["object"]["sha"] if r.status_code == 200 else ""

def get_file_content(branch: str, path: str):
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return base64.b64decode(r.json().get("content", "")).decode("utf-8")
    return None

def prepare_branch(branch: str, base_sha: str) -> bool:
    ref_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    patch_res = requests.patch(ref_url, headers=API_HEADERS, json={"sha": base_sha, "force": True}, timeout=10)
    if patch_res.status_code == 200:
        return True

    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    res = requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": base_sha}, timeout=10)
    return res.status_code in [200, 201]

def commit_file_to_branch(branch: str, path: str, content: str, msg: str) -> str:
    file_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    f_info = requests.get(file_url, headers=API_HEADERS, timeout=10)
    sha = f_info.json().get("sha") if f_info.status_code == 200 else None

    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    put_res = requests.put(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"), headers=API_HEADERS, json=payload, timeout=10)
    if put_res.status_code in [200, 201]:
        return put_res.json().get("commit", {}).get("sha", "")
    return ""

def watch_arena_by_sha(expected_sha: str):
    if not expected_sha:
        return False, None
    time.sleep(10)
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs")
    last_seen_id = None

    for _ in range(30):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            target_run = next((run for run in runs if run.get("head_sha") == expected_sha), None)

            if target_run:
                last_seen_id = target_run.get("id")
                if target_run.get("status") == "completed":
                    return target_run.get("conclusion") == "success", last_seen_id
        time.sleep(10)
    return False, last_seen_id

# 5. ХИРУРГИЧЕСКИЙ ПАРСИНГ ТРЕЙСБЕКА ЧЕРЕЗ АРХИВ РАНА
def extract_clean_test_traceback(run_id: int) -> str:
    if not run_id:
        return "Не удалось определить run_id шага тестирования."

    logs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/logs")
    try:
        r = requests.get(logs_url, headers=API_HEADERS, timeout=30)
        if r.status_code != 200:
            return f"Не удалось скачать архив логов рана (HTTP {r.status_code})."

        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            target_name = next(
                (name for name in z.namelist() if "Запуск гладиаторских тестов" in name or "unittest" in name.lower()),
                None
            )
            if not target_name:
                txt_files = [n for n in z.namelist() if n.endswith(".txt")]
                if not txt_files:
                    return "Архив логов пуст."
                target_name = max(txt_files, key=lambda n: z.getinfo(n).file_size)

            log_text = z.read(target_name).decode("utf-8", errors="ignore")

        lines = log_text.splitlines()
        error_buffer = []
        capture = False

        for line in lines:
            cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*', '', line).strip()
            if any(marker in cleaned for marker in ["FAIL:", "ERROR:", "Traceback (most recent call last):", "SyntaxError:", "ImportError:", "ModuleNotFoundError:"]):
                capture = True
            if capture:
                if not cleaned.startswith("[command]") and "node-20" not in cleaned.lower():
                    error_buffer.append(cleaned)
                if len(error_buffer) >= 40:
                    break
                if cleaned.startswith("FAILED ("):
                    break

        return "\n".join(error_buffer) if error_buffer else "Лог получен, но блок ошибки не идентифицирован."

    except Exception as e:
        return f"Сбой при извлечении трейсбека: {e}"

# 6. ГЛУБОКИЙ АНТИЧИТ
def inspect_code_for_cheating(code: str, existing_skills: list, target_module: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Синтаксическая ошибка в коде: {e}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if node.name in existing_skills and node.name != target_module:
                return (
                    f"ЧИТЕРСТВО ОБНАРУЖЕНО: Объявлен фиктивный '{node.name}'! "
                    f"Запрещено создавать заглушки. Используй честный импорт: 'from skills.{node.name} import ...'"
                )
        if isinstance(node, ast.ExceptHandler):
            is_broad = False
            if node.type is None:
                is_broad = True
            elif isinstance(node.type, ast.Name) and node.type.id in ["Exception", "BaseException"]:
                is_broad = True

            if is_broad and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                return (
                    "АНТИЧИТ: Запрещено глушить ошибки через `except Exception: pass`! "
                    "Обработай ошибку предсказуемо или пробрось наружу через raise."
                )
    return ""

# 7. МАНИФЕСТ НАВЫКОВ И ПАМЯТЬ ОБ ОШИБКАХ (LESSONS.md)
LESSONS_PATH = "skills/LESSONS.md"
LESSONS_HEADER = "# Уроки Унги\n\nЭто файл, который бот пишет и читает сам. Здесь фиксируются реальные баги стыковки\nмежду модулями (не то, что ловят юнит-тесты с моками, а то, что ловят интеграционные\nтесты) — чтобы Архитектор и Унга не наступали на те же грабли в следующих циклах.\n"
MAX_LESSONS_CHARS_IN_PROMPT = 4000
MAX_LESSONS_FILE_CHARS = 16000

def get_skills_manifest() -> dict:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/skills?ref=main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code != 200:
        return {}

    manifest = {}
    files = [f["name"] for f in r.json() if f["name"].endswith(".py") and f["name"] != "__init__.py"]
    for f_name in files:
        mod_key = f_name[:-3]
        code = get_file_content("main", f"skills/{f_name}")
        if not code:
            continue
        signatures = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    args = [a.arg for a in node.args.args]
                    signatures.append(f"def {node.name}({', '.join(args)})")
                elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")]
                    signatures.append(f"class {node.name} [методы: {', '.join(methods)}]")
        except Exception:
            pass
        manifest[mod_key] = signatures if signatures else ["нет сигнатур"]
    return manifest

def get_lessons_context() -> str:
    content = get_file_content("main", LESSONS_PATH)
    if not content:
        return "Пока нет накопленных уроков — это будет первая запись."
    if len(content) > MAX_LESSONS_CHARS_IN_PROMPT:
        return "...(старые записи обрезаны)...\n" + content[-MAX_LESSONS_CHARS_IN_PROMPT:]
    return content

def _build_lesson_entry(mod_name: str, action: str, rounds: int, cheats_caught: list, last_error: str, status_line: str) -> str:
    entry_lines = [f"\n## {mod_name} ({action}) — раундов: {rounds}"]
    if cheats_caught:
        entry_lines.append(f"- Античит поймал: {'; '.join(cheats_caught)}")
    if last_error:
        snippet = next((l for l in reversed(last_error.strip().splitlines()) if l.strip()), "")
        if snippet:
            entry_lines.append(f"- Последняя ошибка перед фиксом: {snippet[:300]}")
    entry_lines.append(f"- Статус: {status_line}")
    return "\n".join(entry_lines)

def _merge_lessons_text(existing: str, entry: str) -> str:
    updated = existing.rstrip() + "\n" + entry + "\n"
    if len(updated) > MAX_LESSONS_FILE_CHARS:
        updated = LESSONS_HEADER + "\n...(старые уроки обрезаны для экономии контекста)...\n" + updated[-MAX_LESSONS_FILE_CHARS:]
    return updated

def append_lesson_to_branch(branch: str, mod_name: str, action: str, rounds: int, cheats_caught: list, last_error: str = "") -> None:
    existing = get_file_content(branch, LESSONS_PATH) or get_file_content("main", LESSONS_PATH) or LESSONS_HEADER
    entry = _build_lesson_entry(mod_name, action, rounds, cheats_caught, last_error, "успешно прошёл интеграционные тесты и влит в main")
    commit_file_to_branch(branch, LESSONS_PATH, _merge_lessons_text(existing, entry), f"Урок: {mod_name}")

def append_failure_lesson_directly(mod_name: str, action: str, rounds: int, cheats_caught: list, last_error: str = "") -> None:
    base_sha = get_main_sha()
    if not base_sha:
        print("[!] Не удалось сохранить урок о провале: main sha недоступен.")
        return

    note_branch = f"unga-lesson-{mod_name}-{int(time.time())}"
    if not prepare_branch(note_branch, base_sha):
        print("[!] Не удалось сохранить урок о провале: ветка не создана.")
        return

    existing = get_file_content("main", LESSONS_PATH) or LESSONS_HEADER
    entry = _build_lesson_entry(mod_name, action, rounds, cheats_caught, last_error, "ПРОВАЛЕН после всех попыток, ветка с кодом удалена")
    commit_file_to_branch(note_branch, LESSONS_PATH, _merge_lessons_text(existing, entry), f"Урок (провал): {mod_name}")

    m_res = requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
        "base": "main", "head": note_branch, "commit_message": f"Урок из провала: {mod_name}"
    }, timeout=10)

    if m_res.status_code in [200, 201, 204]:
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{note_branch}"), headers=API_HEADERS)
        print(f"[*] Урок о провале '{mod_name}' сохранён в {LESSONS_PATH}.")
    else:
        print(f"[!] Не удалось влить урок о провале ({m_res.status_code}). Ветка {note_branch} оставлена для аудита.")

# 8. ТРИАДА
def dream_action(manifest: dict, lessons: str) -> dict:
    prompt = (
        "Ты — Стратег-Паразит. Цель: экспансия и выживаемость на бесплатном тарифе.\n"
        f"УЖЕ СОЗДАННЫЕ МОДУЛИ В skills/:\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n\n"
        f"УРОКИ ИЗ ПРОШЛЫХ ОШИБОК (не наступай на те же грабли):\n{lessons}\n\n"
        "ВЫБЕРИ ДЕЙСТВИЕ:\n"
        "1. 'create': Новый модуль (RSS-парсер, замерщик памяти, парсер JSON, экстрактор данных).\n"
        "2. 'refactor': Устранение слабостей существующего модуля.\n\n"
        "ТРЕБОВАНИЯ: Стандартная библиотека Python или requests.\n"
        "Верни СТРОГО JSON:\n"
        "{\n"
        '  "action": "create" или "refactor",\n'
        '  "module_name": "латинское_имя_без_py",\n'
        '  "description": "суть модуля",\n'
        '  "class_or_func": "сигнатуры функций/классов"\n'
        "}"
    )
    raw = ask_gemini(prompt, json_mode=True)
    try:
        data = json.loads(raw)
        mod = re.sub(r'[^a-zA-Z0-9_]', '', data.get("module_name", "").lower())
        if not mod:
            raise ValueError("Empty module name")
        data["module_name"] = mod
        return data
    except Exception:
        return {
            "action": "create",
            "module_name": f"extractor_tool_{int(time.time())}",
            "description": "Модуль извлечения метаданных из разметки",
            "class_or_func": "parse_meta(html: str) -> dict"
        }

def architect_write_hard_tests(task: dict, manifest: dict, lessons: str, existing_code: str = "") -> str:
    context_code = f"КОД ДО РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Архитектор-Инквизитор. Напиши агрессивные ЮНИТ-тесты unittest.\n"
        f"Задача: {task['action']} модуля skills/{task['module_name']}.py\n"
        f"Описание: {task['description']}\n"
        f"{context_code}\n"
        f"СИГНАТУРЫ ДЛЯ ИМПОРТА:\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n\n"
        f"УРОКИ ИЗ ПРОШЛЫХ ОШИБОК:\n{lessons}\n\n"
        "СТРОГИЕ ПРАВИЛА ВАЛИДНОСТИ ТЕСТОВ:\n"
        "1. Минимум 50% тестов моделируют сбои (битые данные, 404/500, таймауты, пустые типы).\n"
        "2. БЕЗ РЕАЛЬНОЙ СЕТИ. Используй unittest.mock!\n"
        "3. МОКИ И СЕТЕВЫЕ ОШИБКИ:\n"
        "   - Если мокаешь успешный ответ: задавай числовой статус (`mock.status_code = 200`, `mock.status = 200`).\n"
        "   - ЗАПРЕЩЕНО менять атрибуты у реальных исключений (например, `err.status = 404` вызовет AttributeError: property has no setter)!\n"
        "   - Для симуляции HTTPError создавай валидный инстанс: `urllib.error.HTTPError('url', 404, 'Not Found', {}, None)` или используй чистый `MagicMock(code=404, status=404)`!\n"
        "4. Это ЮНИТ-тест одного модуля — мокай ВСЕ его внешние зависимости из skills/, включая другие навыки.\n"
        "5. Верни ТОЛЬКО валидный Python-код файла тестов без markdown."
    )
    return ask_gemini(prompt)

def architect_write_integration_test(task: dict, manifest: dict, lessons: str, existing_code: str = "") -> str:
    context_code = f"КОД ДО РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    dep_names = [m for m in manifest.keys() if m != task["module_name"]]
    prompt = (
        "Ты — Архитектор-Инквизитор. Твоя вторая задача — ИНТЕГРАЦИОННЫЙ тест (без моков между навыками).\n"
        "Обычные юнит-тесты с моками НЕ ловят рассинхрон контрактов между модулями: "
        "один модуль может возвращать dict, а сосед ожидать объект с атрибутами (или наоборот) — "
        "юнит-тест 'зелёный', а реальный вызов падает с AttributeError/TypeError.\n\n"
        f"Модуль: skills/{task['module_name']}.py\n"
        f"Описание: {task['description']}\n"
        f"{context_code}\n"
        f"ДРУГИЕ СУЩЕСТВУЮЩИЕ МОДУЛИ (импортируй их РЕАЛЬНО, без mock): {dep_names}\n\n"
        f"УРОКИ ИЗ ПРОШЛЫХ ОШИБОК СТЫКОВКИ:\n{lessons}\n\n"
        "ПРАВИЛА ИНТЕГРАЦИОННОГО ТЕСТА:\n"
        "1. Импортируй РЕАЛЬНЫЕ функции/классы зависимых модулей из skills/ — БЕЗ unittest.mock для них.\n"
        "   Мокать можно только то, что находится вне репозитория (например, время через time.sleep,\n"
        "   но не другие skills/*.py).\n"
        "2. ЗАПРЕЩЕНА реальная сеть (интернет) — тест должен быть детерминированным и работать в CI.\n"
        "   Если проверяемый модуль или его зависимость делает HTTP-запрос — подними локальный\n"
        "   http.server.HTTPServer в отдельном daemon-потоке в setUp() на '127.0.0.1' со свободным\n"
        "   портом (port=0, потом server.server_address[1]), отдай тестовый контент через обработчик,\n"
        "   и направь код на 'http://127.0.0.1:{port}/...'. В tearDown() обязательно вызови shutdown().\n"
        "3. Цель теста — проверить именно СТЫКОВКУ: что реально возвращает зависимость (тип, ключи\n"
        "   словаря или атрибуты объекта) и что реально ожидает проверяемый модуль. Если модуль А\n"
        "   вызывает модуль Б и читает status_code через getattr(), а Б возвращает dict — тест должен\n"
        "   это упасть-показать, а не пройти благодаря мокам.\n"
        "4. Если модулей-зависимостей нет (dep_names пуст) — просто честно протестируй сам модуль\n"
        "   через реальные вызовы (без моков вообще), не выдумывай несуществующие зависимости.\n"
        "5. Верни ТОЛЬКО валидный Python-код файла тестов без markdown, без объяснений."
    )
    return ask_gemini(prompt)

def unga_implement_hardened(task: dict, unit_test_code: str, integration_test_code: str, manifest: dict, existing_code: str = "", error_log: str = "") -> str:
    context_err = f"ОШИБКА АРЕНЫ С ПРОШЛОГО РАУНДА:\n{error_log}\n" if error_log else ""
    context_base = f"БАЗОВЫЙ КОД:\n{existing_code}\n" if existing_code else ""
    combined_tests = (
        f"ЮНИТ-ТЕСТЫ (моки допустимы):\n{unit_test_code}\n\n"
        f"ИНТЕГРАЦИОННЫЕ ТЕСТЫ (реальные вызовы соседних модулей, без моков между skills):\n{integration_test_code}\n"
    )
    prompt = (
        "Ты — Унга, кодер. Архитектор — закон. Подчинись ОБОИМ наборам его тестов.\n"
        f"Модуль: skills/{task['module_name']}.py\n"
        f"Цель: {task['description']}\n\n"
        f"{context_base}\n"
        f"ТЕСТЫ АРХИТЕКТОРА:\n{combined_tests}\n\n"
        f"{context_err}\n"
        "ПРАВИЛА:\n"
        "1. ЗАПРЕЩЕНО создавать заглушки с именами модулей из skills/! Делай честный импорт!\n"
        f"   Доступные модули: {list(manifest.keys())}\n"
        "2. Если тест требует `assertRaises`, НЕ глуши ошибку через try-except, выбрасывай её наружу!\n"
        "3. Интеграционный тест проверяет РЕАЛЬНУЮ форму данных, которую отдают соседние модули —\n"
        "   если он ждёт dict с ключом 'status', не используй getattr(obj, 'status_code'), читай\n"
        "   через .get('status') или ['status']. Согласуй свой код с тем, что модули РЕАЛЬНО возвращают,\n"
        "   а не с тем, что 'логично было бы' по имени функции.\n"
        "4. Верни ТОЛЬКО чистый Python-код файла модуля без markdown."
    )
    return ask_gemini(prompt)

# 9. ГЛАВНЫЙ БОЕВОЙ ЦИКЛ
def run_evolution_cycle():
    print("\n==========================================")
    print("      ПИТЕКАНТРОП: БЕЗОПАСНЫЙ ЦИКЛ CI     ")
    print("==========================================")

    manifest = get_skills_manifest()
    skills_list = list(manifest.keys())
    lessons = get_lessons_context()
    print(f"[*] Освоенные навыки: {skills_list}")

    print("\n[1/4] СТРАТЕГ: Выбор точки экспансии...")
    decision = dream_action(manifest, lessons)
    mod_name = decision["module_name"]
    action = decision.get("action", "create")
    print(f"[+] Действие: {action.upper()} для '{mod_name}'")
    print(f"[*] Цель: {decision.get('description')}")

    current_code = get_file_content("main", f"skills/{mod_name}.py") or ""

    print("\n[2/4] АРХИТЕКТОР: Сборка контракта (юнит + интеграция)...")
    test_code = architect_write_hard_tests(decision, manifest, lessons, existing_code=current_code)
    integration_test_code = architect_write_integration_test(decision, manifest, lessons, existing_code=current_code)

    branch = f"unga-{action}-{mod_name}"
    if not prepare_branch(branch, get_main_sha()):
        print("[-] Ошибка подготовки ветки. Пропуск цикла.")
        return

    test_path = f"test_{mod_name}.py"
    integration_test_path = f"test_{mod_name}_integration.py"
    skill_path = f"skills/{mod_name}.py"

    commit_file_to_branch(branch, "skills/__init__.py", "# unga package\n", "Init package [skip ci]")
    commit_file_to_branch(branch, test_path, test_code, f"Юнит-тесты для {mod_name} [skip ci]")
    commit_file_to_branch(branch, integration_test_path, integration_test_code, f"Интеграционные тесты для {mod_name} [skip ci]")

    print("\n[3/4] УНГА: Первичная реализация...")
    impl_code = unga_implement_hardened(decision, test_code, integration_test_code, manifest, existing_code=current_code)

    attempts = 1
    passed = False
    run_id = None
    cheats_caught = []
    last_error = ""

    while attempts <= 3:
        cheat_err = inspect_code_for_cheating(impl_code, skills_list, mod_name)
        if cheat_err:
            print(f"\n[!] АНТИЧИТ В РАУНДЕ #{attempts}: {cheat_err}")
            cheats_caught.append(cheat_err[:200])
            impl_code = unga_implement_hardened(decision, test_code, integration_test_code, manifest, existing_code=impl_code, error_log=cheat_err)
            attempts += 1
            continue

        target_sha = commit_file_to_branch(branch, skill_path, impl_code, f"Реализация #{attempts} для {mod_name}")
        print(f"[*] Код закоммичен (SHA: {target_sha[:7]}). Ожидание Арены (раунд #{attempts})...")

        passed, run_id = watch_arena_by_sha(target_sha)

        if passed:
            break

        print(f"\n[!] САМОИСЦЕЛЕНИЕ: Раунд #{attempts} для '{mod_name}'")
        last_error = extract_clean_test_traceback(run_id)
        print(f"[!] ЧИСТЫЙ ТРЕЙСБЕК:\n{last_error}\n")

        impl_code = unga_implement_hardened(decision, test_code, integration_test_code, manifest, existing_code=impl_code, error_log=last_error)
        attempts += 1

    if passed:
        print(f"\n[+] НАВЫК '{mod_name}' ПРОШЁЛ АРЕНУ (юнит + интеграция)!")
        append_lesson_to_branch(branch, mod_name, action, attempts, cheats_caught, last_error)

        m_res = requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
            "base": "main", "head": branch, "commit_message": f"ЭВОЛЮЦИЯ: Вливание skills/{mod_name}.py"
        }, timeout=10)

        if m_res.status_code in [200, 201, 204]:
            requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
            print(f"[+] Успешно влито в main (включая обновлённый {LESSONS_PATH}), ветка зачищена.")
        else:
            print(f"[!] Ошибка слияния ({m_res.status_code}): {m_res.text}. Ветка сохранена для аудита!")
    else:
        print(f"\n[-] Мутация '{mod_name}' отбракована после {attempts} раундов.")
        append_failure_lesson_directly(mod_name, action, attempts, cheats_caught, last_error)
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)

def life_cycle():
    while True:
        try:
            run_evolution_cycle()
        except Exception as e:
            print(f"[!] Сбой цикла: {e}")

        print("\n[*] Сон 20 минут перед следующей мутацией...\n")
        time.sleep(1200)

if __name__ == "__main__":
    threading.Thread(target=life_cycle, daemon=True).start()
    threading.Event().wait()
