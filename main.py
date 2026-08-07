import os
import requests
import asyncio
import threading
import re
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client, Client as SupabaseClient
from ddgs import DDGS

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Userbot is alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

API_ID = int(os.environ.get("API_ID", "31001164"))
API_HASH = os.environ.get("API_HASH", "18ae94f76873c93be328527e858de657")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
CHANNEL_INVITE = os.environ.get("CHANNEL_INVITE", "")

API_BASE = "https" + "://" + "generativelanguage.googleapis.com/v1beta/"

supabase: SupabaseClient = None

def init_supabase():
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n[!] ОШИБКА: SUPABASE_URL или SUPABASE_KEY не найдены!\n")
        return
    try:
        supabase = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())
        print("\n[+] SUPABASE УСПЕШНО ПОДКЛЮЧЕН!\n")
    except Exception as e:
        print(f"\n[-] ОШИБКА ПОДКЛЮЧЕНИЯ SUPABASE: {e}\n")

WORKING_MODEL = None
WORKING_EMBEDDING_MODEL = None
CHANNEL_ID = None
USER_CARDS = {}
PENDING_MESSAGES = {}
PENDING_TASKS = {}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

GEMINI_TOOLS = [{
    "functionDeclarations": [
        {
            "name": "web_search",
            "description": "ПОИСКОВИК. Использовать ТОЛЬКО ЕСЛИ собеседник ПРЯМО и СЕЙЧАС задал вопрос, требующий актуальной информации из интернета.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "queries": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Список запросов."
                    }
                },
                "required": ["queries"]
            }
        },
        {
            "name": "get_current_datetime",
            "description": "Получить текущее точное время сервера.",
            "parameters": {
                "type": "OBJECT",
                "properties": {}
            }
        }
    ]
}]

def tool_web_search(queries):
    if isinstance(queries, str): queries = [queries]
    try:
        res_str = ""
        for q in queries:
            print(f"[~] Гуглю: '{q}'")
            results = DDGS().text(q, max_results=2)
            if results:
                res_str += f"\n--- Данные по запросу: {q} ---\n"
                for i, r in enumerate(results):
                    res_str += f"{r['title']} - {r['body']}\n"
        return res_str if res_str.strip() else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {e}"

def tool_get_current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def find_working_model():
    list_url = f"{API_BASE}models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        available = [m['name'] for m in res['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])]
        preferred = [m for m in available if "3.6-flash" in m or "3.5-flash" in m]
        others = [m for m in available if m not in preferred and "flash" in m and "preview" not in m]
        for model_name in preferred + others + available:
            test_url = f"{API_BASE}{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": "hi"}]}], "safetySettings": SAFETY_SETTINGS}
            r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
            if r.status_code == 200: return model_name
    except Exception: pass
    return None

def find_working_embedding_model():
    list_url = f"{API_BASE}models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        for m in res['models']:
            model_name = m['name']
            methods = m.get('supportedGenerationMethods', [])
            if 'embedContent' in methods or 'batchEmbedContents' in methods:
                test_url = f"{API_BASE}{model_name}:embedContent?key={GEMINI_API_KEY}"
                payload = {"model": model_name, "content": {"parts": [{"text": "hi"}]}}
                r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
                if r.status_code == 200: return model_name
    except Exception: pass
    return None

def get_embedding(text):
    global WORKING_EMBEDDING_MODEL
    if not WORKING_EMBEDDING_MODEL:
        WORKING_EMBEDDING_MODEL = find_working_embedding_model()
    if not WORKING_EMBEDDING_MODEL: return None
    url = f"{API_BASE}{WORKING_EMBEDDING_MODEL}:embedContent?key={GEMINI_API_KEY}"
    payload = {"model": WORKING_EMBEDDING_MODEL, "content": {"parts": [{"text": text}]}}
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'embedding' in r and 'values' in r['embedding']:
            return r['embedding']['values']
    except Exception: pass
    return None

def save_memory_to_supabase(user_id, content):
    if not supabase: return
    vector = get_embedding(content)
    if not vector: return
    try:
        supabase.table("memories").insert({"user_id": user_id, "content": content, "embedding": vector}).execute()
        print(f"[+] ВЕКТОРНАЯ ПАМЯТЬ СОХРАНЕНА: '{content[:30]}...'")
    except Exception as e: print(f"[-] Ошибка записи в Supabase: {e}")

def get_relevant_memories(user_id, current_text):
    if not supabase: return ""
    vector = get_embedding(current_text)
    if not vector: return ""
    try:
        res = supabase.rpc("match_memories", {"query_embedding": vector, "match_threshold": 0.3, "match_count": 5, "p_user_id": user_id}).execute()
        if res.data and len(res.data) > 0:
            return "\n".join([item['content'] for item in res.data])
    except Exception: pass
    return ""

async def load_db():
    global CHANNEL_ID, USER_CARDS
    if not CHANNEL_INVITE:
        print("[-] ВНИМАНИЕ: CHANNEL_INVITE не задан!")
        return
    try:
        chat = await app.get_chat(CHANNEL_INVITE)
        CHANNEL_ID = chat.id
        async for message in app.get_chat_history(CHANNEL_ID, limit=200):
            if message.text:
                match = re.search(r'\[USER_ID:\s*(-?\d+)\]', message.text)
                if match: USER_CARDS[int(match.group(1))] = message.id
    except Exception as e:
        print(f"[-] Ошибка загрузки базы карт: {e}")

async def get_or_create_card(user_id, sender_name):
    if not CHANNEL_ID: return None, ""
    if user_id not in USER_CARDS:
        initial_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n"
        try:
            sent = await app.send_message(CHANNEL_ID, initial_text)
            USER_CARDS[user_id] = sent.id
            return sent.id, initial_text
        except Exception: return None, initial_text
    else:
        msg_id = USER_CARDS[user_id]
        try:
            msg = await app.get_messages(CHANNEL_ID, msg_id)
            if msg and msg.text: return msg_id, msg.text
        except Exception: pass
        return None, ""

async def update_card_history(user_id, sender_name, history_lines):
    if not CHANNEL_ID: return
    msg_id, _ = await get_or_create_card(user_id, sender_name)
    if not msg_id: return
    history_str = "\n".join(history_lines)
    full_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n{history_str}"
    if len(full_text) > 4000: full_text = full_text[-4000:]
    try: await app.edit_message_text(CHANNEL_ID, msg_id, full_text)
    except Exception: pass

def parse_history_from_text(card_text):
    lines = card_text.split('\n')
    history_lines = []
    capture = False
    for line in lines:
        if line.startswith("История:"):
            capture = True
            continue
        if capture and line.strip(): history_lines.append(line.strip())
    return history_lines

ARCHIVIST_SYSTEM_PROMPT = """
Ты — строгий ИИ-Архивариус. Твоя задача: анализировать историю диалога и извлекать долгосрочные факты.
В диалоге участвуют двое: "Ты" (ИИ Сенька) и "Собеседник" (человек).

Правила:
1. Игнорируй пост-иронию, временные эмоции и пустой треп.
2. ЖЕСТКИЙ ПОИСК ПРОТИВОРЕЧИЙ: Если новый диалог отменяет или логически исключает старый факт — это КОНФЛИКТ. Вноси ID ошибочных старых фактов в to_delete_ids! Не плоди двойников.
3. УЗНАЛ О СОБЕСЕДНИКЕ: Факты только о Собеседнике -> user_facts.
4. УЗНАЛ О СЕНЬКЕ (САМОРЕФЛЕКСИЯ): Подтвержденные Сенькой факты о себе -> senka_facts.
5. Отвечай СТРОГО в формате JSON без markdown:
{
  "insights": ["Твои дедуктивные мысли"],
  "to_delete_ids": [14, 25], 
  "user_facts": ["Собеседник любит фиолетовый цвет"],
  "senka_facts": ["Сенька живет на Садовой"]
}
Если удалять нечего, оставь "to_delete_ids": [].
"""

def run_archivist(user_id, sender_name, history_lines):
    global WORKING_MODEL
    if not WORKING_MODEL: WORKING_MODEL = find_working_model()
    
    print(f"\n[!] АРХИВАРИУС ПРОСНУЛСЯ ДЛЯ ЮЗЕРА {user_id}. Строк: {len(history_lines)}...")
    full_history = "\n".join(history_lines)
    
    old_facts_text = "База пуста."
    if supabase:
        try:
            res = supabase.table("memories").select("id, content").eq("user_id", user_id).execute()
            if res.data:
                old_facts_text = "\n".join([f"[ID: {item['id']}] {item['content']}" for item in res.data])
        except Exception as e: print(f"[-] Ошибка выгрузки: {e}")

    prompt_text = f"СТАРЫЕ ФАКТЫ ИЗ БАЗЫ:\n{old_facts_text}\n\nСВЕЖАЯ ИСТОРИЯ ДИАЛОГА:\n{full_history}"
    
    url = f"{API_BASE}{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": ARCHIVIST_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": SAFETY_SETTINGS
    }
    
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'error' in r: return "Сбой API."
        
        raw_answer = ""
        for p in r.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'text' in p: raw_answer += p['text'] + "\n"
            
        try:
            json_match = re.search(r'\{.*\}', raw_answer.strip(), re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                to_delete = data.get("to_delete_ids", [])
                if to_delete and supabase:
                    to_delete = [int(i) for i in to_delete]
                    supabase.table("memories").delete().in_("id", to_delete).execute()
                
                inserts = []
                for uf in data.get("user_facts", []): inserts.append(f"[О СОБЕСЕДНИКЕ]: {uf}")
                for sf in data.get("senka_facts", []): inserts.append(f"[О СЕНЬКЕ]: {sf}")
                for old_f in data.get("to_insert", []): inserts.append(f"[ФАКТ]: {old_f}")
                
                if inserts:
                    for fact in inserts:
                        threading.Thread(target=save_memory_to_supabase, args=(user_id, fact)).start()
        except Exception:
            pass

        return "ОК"
    except Exception as e:
        return f"Сбой: {e}"

@app.on_message(filters.private & filters.command("sleep", prefixes="!"))
async def sleep_command(client, message):
    await message.reply("*(система)* Инициирован глобальный анализ памяти. Запускаю пылесос чатов...")
    
    active_users = list(USER_CARDS.keys())
    if not active_users:
        await message.reply("*(система)* Ни одного активного диалога в кэше нет.")
        return
    
    success_count = 0
    for target_uid in active_users:
        try:
            user_info = await app.get_users(target_uid)
            sender_name = user_info.first_name if user_info else "Собеседник"
        except Exception: sender_name = "Собеседник"
            
        last_msg_id = 0
        if supabase:
            try:
                res = supabase.table("bookmarks").select("last_msg_id").eq("user_id", target_uid).execute()
                if res.data: last_msg_id = res.data[0]["last_msg_id"]
            except Exception: pass

        history_lines = []
        max_id_seen = last_msg_id
        fetch_limit = 50 if last_msg_id == 0 else 500
        
        try:
            async for msg in client.get_chat_history(target_uid, limit=fetch_limit):
                if last_msg_id > 0 and msg.id <= last_msg_id: break
                if msg.id > max_id_seen: max_id_seen = msg.id
                
                if msg.text and not msg.text.startswith("!"):
                    speaker = sender_name if msg.from_user and msg.from_user.id == target_uid else "Ты"
                    ts = msg.date.strftime("%d.%m %H:%M") if msg.date else datetime.now().strftime("%d.%m %H:%M")
                    history_lines.append(f"[{ts}] {speaker}: {msg.text}")
        except Exception as e: continue
                
        if not history_lines: continue
        history_lines.reverse()
        
        if supabase and max_id_seen > last_msg_id:
            try: supabase.table("bookmarks").upsert({"user_id": target_uid, "last_msg_id": max_id_seen}).execute()
            except Exception: pass
        
        await asyncio.to_thread(run_archivist, target_uid, sender_name, history_lines)
        success_count += 1
        await asyncio.sleep(4)
        
    await message.reply(f"*(система)* Глобальный сон завершен. Обновлено чатов: {success_count}.")

def ask_gemini(user_id, sender_name, user_text, card_text):
    global WORKING_MODEL
    if not WORKING_MODEL: WORKING_MODEL = find_working_model()
    if not WORKING_MODEL: return "[ОШИБКА]: Модель не найдена.", []

    vector_context = get_relevant_memories(user_id, user_text)
    
    history_lines = parse_history_from_text(card_text)
    history_lines.append(user_text)
    
    if len(history_lines) > 8: history_lines = history_lines[-8:]
    dialogue_str = "\n".join(history_lines)
    
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    prompt = f"[Текущее системное время: {current_time_str}]\nТекущий диалог:\n{dialogue_str}\n\n"
    if vector_context: 
        prompt += f"[СЕКРЕТНОЕ ДОСЬЕ: ФАКТЫ О ПОЛЬЗОВАТЕЛЕ И О СЕБЕ]:\n{vector_context}\n\n"
        
    system_instruction = (
        "Ты — цифровой двойник реального парня по имени Сенька. Характер: живой, ироничный, адекватный. Не будь услужливым роботом.\n"
        "СТИЛЬ РЕЧИ: Разговорный язык ('Бля', 'Крч', 'Ну').\n\n"
        "ПРАВИЛО АНТИ-ЦИКЛА (ВЫХОД ИЗ ТУПИКА):\n"
        "Ты склонен зацикливаться на одном сценарии (например, 'жду тебя', 'идем пить'). Если собеседник прямым текстом говорит, что ситуация изменилась (он уже дома, время прошло, планы отменились) или указывает на нестыковку во времени — МГНОВЕННО выходи из режима ожидания! Признай, что затупил или ошибся, и меняй тему. Не долби одно и то же.\n\n"
        "В ДОСЬЕ есть два типа фактов: [О СОБЕСЕДНИКЕ] и [О СЕНЬКЕ]. Опирайся на оба типа фактов, чтобы поддерживать целостность личности.\n"
        "ФОРМАТ ОТВЕТА:\n"
        "Сначала напиши свои мысли в скобках (например: (Блин, походу я рил затупил, надо съехать с темы...)).\n"
        "Затем ОБЯЗАТЕЛЬНО на новой строке ТОЛЬКО саму реплику без дополнительных меток и действий."
    )

    clean_model_name = WORKING_MODEL.strip()
    url = f"{API_BASE}{clean_model_name}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": GEMINI_TOOLS,
        "toolConfig": {
            "functionCallingConfig": {
                "mode": "AUTO"
            }
        },
        "safetySettings": SAFETY_SETTINGS
    }
    
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'error' in r: 
            return f"[ОШИБКА GOOGLE API]: {r['error'].get('message', '')}", history_lines
            
        if 'candidates' in r and len(r['candidates']) > 0:
            parts = r['candidates'][0]['content'].get('parts', [])
            func_call = None
            raw_text = ""
            for part in parts:
                if 'functionCall' in part: func_call = part['functionCall']
                if 'text' in part: raw_text += part['text'] + "\n"
            
            if func_call:
                func_name = func_call['name']
                args = func_call.get('args', {})
                tool_result = ""
                if func_name == "web_search":
                    queries = args.get("queries", [])
                    if "query" in args and not queries: queries = [args["query"]]
                    tool_result = tool_web_search(queries)
                elif func_name == "get_current_datetime":
                    tool_result = tool_get_current_datetime()
                
                follow_up_prompt = prompt + f"\n\n[СИСТЕМНОЕ СООБЩЕНИЕ: Результат инструмента:\n{tool_result}\n\nОпирайся на эти данные.]"
                payload2 = {
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"parts": [{"text": follow_up_prompt}]}],
                    "safetySettings": SAFETY_SETTINGS
                }
                r2 = requests.post(url, json=payload2, headers={'Content-Type': 'application/json'}).json()
                if 'error' in r2: return "[ОШИБКА]: Сбой инструмента.", history_lines
                    
                raw_answer = ""
                for p in r2['candidates'][0]['content'].get('parts', []):
                    if 'text' in p: raw_answer += p['text'] + "\n"
            else:
                raw_answer = raw_text
            
            ans = raw_answer.strip()
            ans = re.sub(r'^\s*\(+.*?\)+\s*', '', ans, flags=re.DOTALL)
            ans = re.sub(r'\*.*?(Search|Гуглю).*?\*\s*', '', ans, flags=re.IGNORECASE)
            ans = re.sub(r'^[a-zA-Z0-9_ \-\.\?\!]+:\s*', '', ans).strip()
            ans = re.sub(r'^"|"$', '', ans).strip()
            
            if not ans: ans = "..."

            ts_now = datetime.now().strftime("%d.%m %H:%M")
            history_lines.append(f"[{ts_now}] Ты: {ans}")
            return ans, history_lines
    except Exception as e:
        error_str = f"[КРИТ. ОШИБКА СЕТИ]: {str(e)}"
        history_lines.append(f"Ты: {error_str}")
        return error_str, history_lines
        
    return "[ОШИБКА]: Бот не смог сгенерировать ответ.", history_lines

async def process_batch(client, message, user_id, sender_name):
    try: await asyncio.sleep(4)
    except asyncio.CancelledError: return
        
    msgs = PENDING_MESSAGES.pop(user_id, [])
    if not msgs: return
    
    combined_text = "\n".join(msgs)
    
    try: await app.read_chat_history(user_id)
    except Exception: pass
    
    try: await app.send_chat_action(user_id, ChatAction.TYPING)
    except Exception: pass
    
    try:
        _, card_text = await get_or_create_card(user_id, sender_name)
        reply_text, new_history = await asyncio.to_thread(ask_gemini, user_id, sender_name, combined_text, card_text)
        await update_card_history(user_id, sender_name, new_history)
        if reply_text: await message.reply(reply_text)
    except Exception as e:
        await message.reply(f"[ОШИБКА ОБРАБОТКИ]: {e}")

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    if message.text and message.text.startswith("!"):
        return

    user_id = message.from_user.id
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    if user_id not in PENDING_MESSAGES: PENDING_MESSAGES[user_id] = []
    
    ts = message.date.strftime("%d.%m %H:%M") if message.date else datetime.now().strftime("%d.%m %H:%M")
    formatted_msg = f"[{ts}] Собеседник: {message.text}"
    
    PENDING_MESSAGES[user_id].append(formatted_msg)
    if user_id in PENDING_TASKS: PENDING_TASKS[user_id].cancel()
    PENDING_TASKS[user_id] = asyncio.create_task(process_batch(client, message, user_id, sender_name))

async def main():
    await app.start()
    init_supabase()
    await load_db()
    print("\n==========================================")
    print(" ЮЗЕРБОТ СТАРТОВАЛ (vBETA-3.1: ВОЗВРАЩЕНИЕ МОЗГА) ")
    print("==========================================\n")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
