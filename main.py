import os
import sys
import time
import base64
import re
import json
import ast
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
        MODELS_CACHE["expires_at"] = 0  # Сбрасываем кэш при смене ключа
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
    # Пытаемся безопасно обновить ref с силой (без race condition удаления)
    patch_res = requests.patch(ref_url, headers=API_HEADERS, json={"sha": base_sha, "force": True}, timeout=10)
    if patch_res.status_code == 200:
        return True
    
    # Если ветки нет — создаем
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
    
    # 30 проверок по 10 сек = до 5 минут честного ожидания раннера
    for _ in range(30):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            target_run = next((run for run in runs if run.get("head_sha") == expected_sha), None)
            
            if target_run:
                run_id = target_run.get("id")
                if target_run.get("status") == "completed":
                    return target_run.get("conclusion") == "success", run_id
        time.sleep(10)
    return False, None

# 5. ХИРУРГИЧЕСКИЙ ПАРСИНГ ТРЕЙСБЕКА С НАЧАЛА ОШИБКИ
def extract_clean_test_traceback(run_id: int) -> str:
    if not run_id:
        return "Не удалось определить run_id шага тестирования."
        
    jobs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/jobs")
    r = requests.get(jobs_url, headers=API_HEADERS, timeout=10)
    if r.status_code != 200:
        return "Не удалось получить список jobs."
    jobs = r.json().get("jobs", [])
    failed = next((j for j in jobs if j.get("conclusion") == "failure"), None)
    if not failed:
        return "Проваленный job не найден."
    
    log_res = requests.get(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/jobs/{failed['id']}/logs"), headers=API_HEADERS, timeout=15)
    if log_res.status_code != 200:
        return "Тело логов недоступно."

    lines = log_res.text.splitlines()
    error_buffer = []
    capture = False

    for line in lines:
        cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*', '', line).strip()
        # Старт захвата при возникновении реального падения
        if any(marker in cleaned for marker in ["FAIL:", "ERROR:", "Traceback (most recent call last):", "SyntaxError:", "ImportError:"]):
            capture = True
        if capture:
            if not cleaned.startswith("[command]") and "node-20" not in cleaned.lower():
                error_buffer.append(cleaned)
            # Если захватили 40 строк с момента старта ошибки — отдаем, это и есть суть падения
            if len(error_buffer) >= 40:
                break
            if cleaned.startswith("FAILED ("):
                break

    if error_buffer:
        return "\n".join(error_buffer)
    return "Тесты провалены, но блок ошибки не идентифицирован."

# 6. ГЛУБОКИЙ АНТИЧИТ ЧЕРЕЗ AST.WALK
def inspect_code_for_cheating(code: str, existing_skills: list, target_module: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Синтаксическая ошибка в коде: {e}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if node.name in existing_skills and node.name != target_module:
                return (
                    f"ЧИТЕРСТВО ОБНАРУЖЕНО: Ты объявил фиктивный '{node.name}'! "
                    f"Запрещено создавать заглушки. Используй честный импорт: 'from skills.{node.name} import ...'"
                )
    return ""

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

# 7. ТРИАДА
def dream_action(manifest: dict) -> dict:
    prompt = (
        "Ты — Стратег-Паразит. Цель: экспансия и выживаемость на бесплатном тарифе.\n"
        f"УЖЕ СОЗДАННЫЕ МОДУЛИ В skills/:\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n\n"
        "ВЫБЕРИ ДЕЙСТВИЕ:\n"
        "1. 'create': Новый модуль (RSS-парсер, ротатор юзер-агентов, замерщик памяти, парсер JSON).\n"
        "2. 'refactor': Устранение слабостей существующего модуля.\n\n"
        "ТРЕБОВАНИЯ: Только стандартная библиотека Python или requests.\n"
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

def architect_write_hard_tests(task: dict, manifest: dict, existing_code: str = "") -> str:
    context_code = f"КОД ДО РЕФАКТОРИНГА:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Архитектор-Инквизитор. Напиши агрессивные юнит-тесты unittest.\n"
        f"Задача: {task['action']} модуля skills/{task['module_name']}.py\n"
        f"Описание: {task['description']}\n"
        f"{context_code}\n"
        f"СИГНАТУРЫ ДЛЯ ИМПОРТА:\n{json.dumps(manifest, indent=2, ensure_ascii=False)}\n\n"
        "ПРАВИЛА ТЕСТОВ:\n"
        "1. 50% тестов проверяют катастрофы (битые данные, 404/500, таймауты, пустые типы).\n"
        "2. БЕЗ РЕАЛЬНОЙ СЕТИ. Используй unittest.mock!\n"
        "3. ВНИМАНИЕ К МОКАМ: Всегда явно задавай числовые статусы мока: `mock.status_code = 200`, `mock.status = 200`!\n"
        "4. Верни ТОЛЬКО валидный Python-код файла тестов без markdown."
    )
    return ask_gemini(prompt)

def unga_implement_hardened(task: dict, test_code: str, manifest: dict, existing_code: str = "", error_log: str = "") -> str:
    context_err = f"ОШИБКА АРЕНЫ С ПРОШЛОГО РАУНДА:\n{error_log}\n" if error_log else ""
    context_base = f"БАЗОВЫЙ КОД:\n{existing_code}\n" if existing_code else ""
    prompt = (
        "Ты — Унга, кодер. Архитектор — закон. Подчинись его тестам.\n"
        f"Модуль: skills/{task['module_name']}.py\n"
        f"Цель: {task['description']}\n\n"
        f"{context_base}\n"
        f"ТЕСТЫ АРХИТЕКТОРА:\n{test_code}\n\n"
        f"{context_err}\n"
        "ПРАВИЛА:\n"
        "1. ЗАПРЕЩЕНО создавать заглушки с именами модулей из skills/! Делай честный импорт!\n"
        f"   Доступные модули: {list(manifest.keys())}\n"
        "2. Если тест требует `assertRaises`, НЕ глуши ошибку через try-except, выбрасывай её наружу!\n"
        "3. Верни ТОЛЬКО чистый Python-код файла модуля без markdown."
    )
    return ask_gemini(prompt)

# 8. ГЛАВНЫЙ БОЕВОЙ ЦИКЛ
def run_evolution_cycle():
    print("\n==========================================")
    print("      ПИТЕКАНТРОП: БЕЗОПАСНЫЙ ЦИКЛ CI     ")
    print("==========================================")
    
    manifest = get_skills_manifest()
    skills_list = list(manifest.keys())
    print(f"[*] Освоенные навыки: {skills_list}")

    print("\n[1/4] СТРАТЕГ: Выбор точки экспансии...")
    decision = dream_action(manifest)
    mod_name = decision["module_name"]
    action = decision.get("action", "create")
    print(f"[+] Действие: {action.upper()} для '{mod_name}'")
    print(f"[*] Цель: {decision.get('description')}")

    current_code = get_file_content("main", f"skills/{mod_name}.py") or ""

    print("\n[2/4] АРХИТЕКТОР: Сборка контракта...")
    test_code = architect_write_hard_tests(decision, manifest, existing_code=current_code)
    
    branch = f"unga-{action}-{mod_name}"
    if not prepare_branch(branch, get_main_sha()):
        print("[-] Ошибка подготовки ветки. Пропуск цикла.")
        return

    test_path = f"test_{mod_name}.py"
    skill_path = f"skills/{mod_name}.py"
    
    commit_file_to_branch(branch, "skills/__init__.py", "# unga package\n", "Init package")
    commit_file_to_branch(branch, test_path, test_code, f"Тесты для {mod_name}")

    print("\n[3/4] УНГА: Первичная реализация...")
    impl_code = unga_implement_hardened(decision, test_code, manifest, existing_code=current_code)
    
    attempts = 1
    passed = False
    run_id = None

    while attempts <= 3:
        cheat_err = inspect_code_for_cheating(impl_code, skills_list, mod_name)
        if cheat_err:
            print(f"\n[!] АНТИЧИТ В РАУНДЕ #{attempts}: {cheat_err}")
            impl_code = unga_implement_hardened(decision, test_code, manifest, existing_code=impl_code, error_log=cheat_err)
            attempts += 1
            continue

        target_sha = commit_file_to_branch(branch, skill_path, impl_code, f"Реализация #{attempts} для {mod_name}")
        print(f"[*] Код закоммичен (SHA: {target_sha[:7]}). Ожидание Арены (раунд #{attempts})...")
        
        passed, run_id = watch_arena_by_sha(target_sha)

        if passed:
            break

        print(f"\n[!] САМОИСЦЕЛЕНИЕ: Раунд #{attempts} для '{mod_name}'")
        err = extract_clean_test_traceback(run_id)
        print(f"[!] ЧИСТЫЙ ТРЕЙСБЕК:\n{err}\n")
        
        impl_code = unga_implement_hardened(decision, test_code, manifest, existing_code=impl_code, error_log=err)
        attempts += 1

    if passed:
        print(f"\n[+] НАВЫК '{mod_name}' ПРОШЕЛ АРЕНУ!")
        m_res = requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
            "base": "main", "head": branch, "commit_message": f"ЭВОЛЮЦИЯ: Вливание skills/{mod_name}.py"
        }, timeout=10)
        
        # Удаляем ветку ТОЛЬКО при успешном слиянии
        if m_res.status_code in [200, 201, 204]:
            requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
            print(f"[+] Успешно влито в main, ветка зачищена.")
        else:
            print(f"[!] Ошибка слияния ({m_res.status_code}): {m_res.text}. Ветка сохранена для аудита!")
    else:
        print(f"\n[-] Мутация '{mod_name}' отбракована.")
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
