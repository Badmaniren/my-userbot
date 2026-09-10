import os
import time
import base64
import re
import json
import ast
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. ЖИЗНЬ КОНТЕЙНЕРА НА RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pithecanthropus Evolution Daemon is running.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. СЕТЬ И КЛЮЧИ GEMINI
def clean_url(url: str) -> str:
    return re.sub(r'\[.*?\]\(|\)', '', url).strip()

API_HOST = "generativelanguage.googleapis.com"
API_BASE = "https://" + API_HOST + "/v1beta/"

GITHUB_HOST = "api.github.com"
GITHUB_BASE = "https://" + GITHUB_HOST + "/repos/"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]
KEY_INDEX = 0

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_current_key():
    global KEY_INDEX
    return API_KEYS[KEY_INDEX % len(API_KEYS)] if API_KEYS else ""

def rotate_key():
    global KEY_INDEX
    if len(API_KEYS) > 1:
        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        print(f"[!] Ротация ключа Gemini -> #{KEY_INDEX}")

def get_viable_models(key: str) -> list:
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
            return viable
    except Exception:
        pass
    return []

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
                    if not json_mode:
                        return re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
                    return ans.strip()
                if r.status_code in [429, 503]:
                    rotate_key()
                    time.sleep(2)
            except Exception:
                time.sleep(2)
    return ""

def get_file_content(branch: str, path: str):
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return base64.b64decode(r.json().get("content", "")).decode("utf-8")
    return None

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
            for node in ast.iter_child_nodes(tree):
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

def get_main_sha() -> str:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    return r.json()["object"]["sha"] if r.status_code == 200 else ""

def prepare_branch(branch: str, base_sha: str):
    del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    requests.delete(del_url, headers=API_HEADERS, timeout=10)
    time.sleep(1)
    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": base_sha}, timeout=10)

def commit_file_to_branch(branch: str, path: str, content: str, msg: str):
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
    requests.put(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"), headers=API_HEADERS, json=payload, timeout=10)

def watch_arena(branch: str, exclude_id=None):
    time.sleep(8)
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs?branch={branch}")
    for _ in range(16):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                run_id = latest.get("id")
                if exclude_id and run_id == exclude_id:
                    time.sleep(4)
                    continue
                if latest.get("status") == "completed":
                    return latest.get("conclusion") == "success", run_id
        time.sleep(5)
    return False, None

def extract_clean_test_traceback(run_id: int) -> str:
    jobs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/jobs")
    r = requests.get(jobs_url, headers=API_HEADERS, timeout=10)
    if r.status_code != 200:
        return ""
    jobs = r.json().get("jobs", [])
    failed = next((j for j in jobs if j.get("conclusion") == "failure"), None)
    if not failed:
        return ""
    
    log_res = requests.get(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/jobs/{failed['id']}/logs"), headers=API_HEADERS, timeout=15)
    if log_res.status_code != 200:
        return ""

    lines = log_res.text.splitlines()
    error_buffer = []
    capture = False

    for line in lines:
        cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*', '', line).strip()
        if any(marker in cleaned for marker in ["FAIL:", "ERROR:", "Traceback (most recent call last):"]):
            capture = True
        if capture:
            if not cleaned.startswith("[command]") and "node-20" not in cleaned.lower():
                error_buffer.append(cleaned)
        if capture and cleaned.startswith("FAILED ("):
            break

    if error_buffer:
        return "\n".join(error_buffer[-35:])
    return "Тесты провалены, traceback не зафиксирован."

# 3. ТРИАДА СОЗНАНИЯ
def dream_action(manifest: dict) -> dict:
    prompt = (
        "Ты — Стратег-Паразит. Твоя цель: максимальная выживаемость и отказоустойчивость агента на бесплатном тарифе.\n"
        f"ТЕКУЩИЕ МОДУЛИ И СИГНАТУРЫ В skills/:\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n\n"
        "ЗАДАЧА: Выбери ОДНО действие из двух:\n"
        "1. 'refactor': Устранение слабостей в существующих модулях (падение на 4xx/5xx в http_ping, несогласованные типы в file_cache).\n"
        "2. 'create': Создание нового прикладного инструмента выживания (парсер RSS, ротатор заголовков, замерщик памяти).\n\n"
        "ТРЕБОВАНИЯ: Только стандартная библиотека Python или requests.\n"
        "Ответь строго JSON-объектом:\n"
        "{\n"
        '  "action": "create" или "refactor",\n'
        '  "module_name": "имя_модуля_без_py",\n'
        '  "description": "что именно делается и почему это критично для выживания",\n'
        '  "class_or_func": "сигнатуры функций/классов"\n'
        "}"
    )
    raw = ask_gemini(prompt, json_mode=True)
    try:
        return json.loads(raw)
    except Exception:
        return {
            "action": "refactor",
            "module_name": "http_ping",
            "description": "Отказоустойчивый пинг с использованием requests или urllib с корректным возвратом 4xx/5xx",
            "class_or_func": "def check_endpoint(url, timeout=5)"
        }

def architect_write_hard_tests(task: dict, manifest: dict, existing_code: str = "") -> str:
    context_code = f"ТЕКУЩАЯ РЕАЛИЗАЦИЯ ДЛЯ РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Архитектор-Инквизитор. Напиши агрессивные юнит-тесты unittest.\n"
        f"Задача: {task['action']} модуля skills/{task['module_name']}.py\n"
        f"Описание: {task['description']}\n"
        f"{context_code}\n"
        f"СПРАВОЧНИК СИГНАТУР ДЛЯ ИМПОРТА:\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n\n"
        "ПРАВИЛА ИНКВИЗИТОРА:\n"
        "1. Минимум 50% тестов моделируют сбои: битые данные, пустые строки, 404/500 ошибки сервера, таймауты.\n"
        "2. НИКАКИХ реальных сетевых запросов! Используй `unittest.mock`.\n"
        "3. ВНИМАНИЕ К МОКАМ: Если мокаешь сетевой ответ, ОБЯЗАТЕЛЬНО настраивай числовой статус-код!\n"
        "   - Если библиотека requests: `mock_resp.status_code = 200`\n"
        "   - Если urllib: настрой И `mock_resp.status = 200`, И `mock_resp.getcode.return_value = 200`!\n"
        "   Не оставляй методы ответов возвращать нечисловой MagicMock!\n"
        "4. Верни ТОЛЬКО валидный Python-код тестов без markdown."
    )
    return ask_gemini(prompt)

def unga_implement_hardened(task: dict, test_code: str, manifest: dict, existing_code: str = "", error_log: str = "") -> str:
    context_err = f"КРИТИЧЕСКИЙ СБОЙ НА АРЕНЕ:\n{error_log}\n" if error_log else ""
    context_base = f"БАЗОВЫЙ КОД ДО РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Унга, рядовой кодер. Архитектор — твой абсолютный господин. Подчинись его тестам.\n"
        f"Модуль: skills/{task['module_name']}.py\n"
        f"Задача: {task['description']}\n\n"
        f"{context_base}\n"
        f"ТЕСТЫ АРХИТЕКТОРА:\n{test_code}\n\n"
        f"{context_err}\n"
        "ПРАВИЛА ВЫЖИВАНИЯ:\n"
        "1. Если тест использует `assertRaises(...)`, НЕ глуши исключение через try-except! Выбрасывай его!\n"
        "2. Если ошибка 'AssertionError: <MagicMock ...> != 200': это значит, что в моке теста лежит другой атрибут! "
        "Для извлечения HTTP-статуса делай надежную проверку: "
        "проверяй `getattr(resp, 'status_code', None)` или `getattr(resp, 'status', None)`, а если вызываешь `.getcode()`, "
        "убедись, что результат — int! Если это не int, бери числовой статус из атрибута `.status`!\n"
        "3. Рекомендуется использовать библиотеку `requests` вместо urllib, если это упрощает код.\n"
        "4. Код обязан пройти ВСЕ тесты до единого.\n"
        "5. Верни ТОЛЬКО чистый код Python без комментариев и markdown."
    )
    return ask_gemini(prompt)

# 4. ЦИКЛ И КУЛДАУН
def run_evolution_cycle():
    print("\n==========================================")
    print("      ПИТЕКАНТРОП: ЦИКЛ ЗАКАЛКИ ЯДРА      ")
    print("==========================================")
    
    manifest = get_skills_manifest()
    print(f"[*] Освоенные навыки: {list(manifest.keys())}")

    print("\n[1/4] СТРАТЕГ: Анализ уязвимостей и выбор вектора...")
    decision = dream_action(manifest)
    mod_name = re.sub(r'[^a-zA-Z0-9_]', '', decision.get("module_name", "tool").lower())
    action = decision.get("action", "create")
    print(f"[+] Действие: {action.upper()} для '{mod_name}'")
    print(f"[*] Причина: {decision.get('description')}")

    current_code = get_file_content("main", f"skills/{mod_name}.py") or ""

    print("\n[2/4] АРХИТЕКТОР: Генерация стресс-тестов...")
    test_code = architect_write_hard_tests(decision, manifest, existing_code=current_code)
    
    branch = f"unga-{action}-{mod_name}"
    prepare_branch(branch, get_main_sha())
    
    test_path = f"test_{mod_name}.py"
    skill_path = f"skills/{mod_name}.py"
    
    commit_file_to_branch(branch, "skills/__init__.py", "# unga skills\n", "Init package")
    commit_file_to_branch(branch, test_path, test_code, f"Стресс-тесты для {mod_name}")

    print("\n[3/4] УНГА: Написание закаленного кода...")
    impl_code = unga_implement_hardened(decision, test_code, manifest, existing_code=current_code)
    commit_file_to_branch(branch, skill_path, impl_code, f"Реализация {mod_name}")

    print(f"[*] Запуск на Арене. Ждем...")
    passed, run_id = watch_arena(branch)
    
    attempts = 1
    while not passed and attempts <= 3:
        print(f"\n[!] САМОИСЦЕЛЕНИЕ: Раунд #{attempts} для '{mod_name}'")
        err = extract_clean_test_traceback(run_id)
        print(f"[!] ЧИСТЫЙ ТРЕЙСБЕК:\n{err}\n")
        
        impl_code = unga_implement_hardened(decision, test_code, manifest, existing_code=impl_code, error_log=err)
        commit_file_to_branch(branch, skill_path, impl_code, f"Исцеление #{attempts}")
        passed, run_id = watch_arena(branch, exclude_id=run_id)
        attempts += 1

    if passed:
        print(f"\n[+] МОДУЛЬ '{mod_name}' ВЫДЕРЖАЛ СТРЕСС-ТЕСТЫ!")
        requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
            "base": "main", "head": branch, "commit_message": f"ЭВОЛЮЦИЯ: Закалка skills/{mod_name}.py ({action})"
        }, timeout=10)
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
        print(f"[+] Успешно влито в main.")
    else:
        print(f"\n[-] Мутация '{mod_name}' не пережила стресс-тесты и уничтожена.")
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)

def life_cycle():
    while True:
        try:
            run_evolution_cycle()
        except Exception as e:
            print(f"[!] Сбой цикла: {e}")
            
        print("\n[*] Сон 20 минут перед следующим циклом отбора...\n")
        time.sleep(1200)

if __name__ == "__main__":
    threading.Thread(target=life_cycle, daemon=True).start()
    threading.Event().wait()
