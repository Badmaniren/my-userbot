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

GEMINI_TOOLS = [{
    "functionDeclarations": [
        {
            "name": "web_search",
            "description": "Искать информацию в Интернете. Вызывай СРАЗУ ЖЕ, если нужны факты, курсы или погода.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "queries": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Список запросов. Пример: ['погода Пермь', 'курс ETH к доллару']"
                    }
                },
                "required": ["queries"]
            }
        },
        {
            "name": "get_current_datetime",
            "description": "Получить текущее точное время и дату сервера.",
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
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        available = [m['name'] for m in res['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])]
        preferred = [m for m in available if "3.6-flash" in m or "3.5-flash" in m]
        others = [m for m in available if m not in preferred and "flash" in m and "preview" not in m]
        for model_name in preferred + others + available:
            test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": "hi"}]}]}
            r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
            if r.status_code == 200: return model_name
    except Exception: pass
    return None

def find_working_embedding_model():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        for m in res['models']:
            model_name = m['name']
            methods = m.get('supportedGenerationMethods', [])
            if 'embedContent' in methods or 'batchEmbedContents' in methods:
                test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:embedContent?key={GEMINI_API_KEY}"
                payload = {"model": model_name, "content": {"parts": [{"text": "hi"}]}}
                r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
                if r.status_code == 200: return model_name
    except Exception: pass
    return None

def get_embedding(text):
    global WORKING_EMBEDDING_MODEL
    if not WORKING_EMBEDDING_MODEL: WORKING_EMBEDDING_MODEL = find_working_embedding_model()
    if not WORKING_EMBEDDING_MODEL: return None
    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_EMBEDDING_MODEL}:embedContent?key={GEMINI_API_KEY}"
    payload = {"model": WORKING_EMBEDDING_MODEL, "content": {"parts": [{"text": text}]}}
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'embedding' in r and 'values' in r['embedding']: return r['embedding']['values']
    except Exception: pass
    return None

def save_memory_to_supabase(user_id, content):
    if not supabase: return
    vector = get_embedding(content)
    if not vector: return
    try:
        supabase.table("memories").insert({"user_id": user_id, "content": content, "embedding": vector}).execute()
        print(f"[+] ФАКТ СОХРАНЕН В БАЗУ: '{content[:30]}...'")
    except Exception as e:
        print(f"[-] Ошибка записи в Supabase: {e}")

def get_relevant_memories(user_id, current_text):
    if not supabase: return ""
    vector = get_embedding(current_text)
    if not vector: return ""
    try:
        res = supabase.rpc("match_memories", {"query_embedding": vector, "match_threshold": 0.3, "match_count": 3, "p_user_id": user_id}).execute()
        if res.data and len(res.data) > 0: return "\n".join([item['content'] for item in res.data])
    except Exception: pass
    return ""

async def load_db():
    global CHANNEL_ID, USER_CARDS
    try:
        chat = await app.get_chat(CHANNEL_INVITE) # Убедись, что переменная CHANNEL_INVITE определена в твоем окружении или коде
        CHANNEL_ID = chat.id
        async for message in app.get_chat_history(CHANNEL_ID, limit=200):
            if message.text:
                match = re.search(r'\[USER_ID:\s*(-?\d+)\]', message.text)
                if match: USER_CARDS[int(match.group(1))] = message.id
    except Exception: pass

def parse_card_info(card_text):
    history_lines = []
    last_msg_id = 0
    sender_name = "Кто-то"
    capture = False
    
    m_name = re.search(r'Имя:\s*(.*)', card_text)
    if m_name: sender_name = m_name.group(1).strip()
        
    m_id = re.search(r'Last_Msg_ID:\s*(\d+)', card_text)
    if m_id: last_msg_id = int(m_id.group(1))

    for line in card_text.split('\n'):
        if line.startswith("История:"): capture = True; continue
        if capture and line.strip(): history_lines.append(line.strip())
            
    return sender_name, last_msg_id, history_lines

async def get_or_create_card(user_id, sender_name):
    if not CHANNEL_ID: return None, "", 0
    if user_id not in USER_CARDS:
        initial_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nLast_Msg_ID: 0\nИстория:\n"
        try:
            sent = await app.send_message(CHANNEL_ID, initial_text)
            USER_CARDS[user_id] = sent.id
            return sent.id, initial_text, 0
        except Exception: return None, initial_text, 0
    else:
        msg_id = USER_CARDS[user_id]
        try:
            msg = await app.get_messages(CHANNEL_ID, msg_id)
            if msg and msg.text:
                _, last_msg_id, _ = parse_card_info(msg.text)
                return msg_id, msg.text, last_msg_id
        except Exception: pass
        return None, "", 0

async def update_card_history(user_id, sender_name, history_lines, last_msg_id):
    if not CHANNEL_ID: return
    msg_id, _, _ = await get_or_create_card(user_id, sender_name)
    if not msg_id: return
    history_str = "\n".join(history_lines)
    full_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nLast_Msg_ID: {last_msg_id}\nИстория:\n{history_str}"
    if len(full_text) > 4000: full_text = full_text[-4000:]
    try: await app.edit_message_text(CHANNEL_ID, msg_id, full_text)
    except Exception: pass

# ==========================================
# МОДУЛЬ "ГЛОБАЛЬНЫЙ НОЧНОЙ АРХИВАРИУС" v3.0
# ==========================================
ARCHIVIST_SYSTEM_PROMPT = """
Ты — хирургически точный ИИ-Архивариус. Твоя задача: обновить векторную базу знаний пользователя.
Тебе предоставлены:
1. ТЕКУЩАЯ БАЗА (у каждого факта есть свой [ID]).
2. НОВЫЙ ДИАЛОГ.

Правила анализа:
1. Игнорируй пост-иронию, спам и рофлы. Выделяй только твердые, новые факты.
2. КОНФЛИКТЫ: Если в новом диалоге есть факт, который опровергает старый факт из базы (например, юзер переехал, или признался, что старый факт был шуткой) — добавь ID старого факта в "to_delete_ids", а новую правду в "to_insert".
3. ДУБЛИКАТЫ: Если факт УЖЕ есть в ТЕКУЩЕЙ БАЗЕ — не добавляй его снова!
4. Выдавай ответ СТРОГО в JSON:
{
  "insights": ["Анализ психологии и контекста"],
  "to_delete_ids": [15, 42],
  "to_insert": ["Свежий проверенный факт 1"]
}
"""

def run_archivist_for_user(user_id, sender_name, new_messages):
    global WORKING_MODEL
    if not WORKING_MODEL: WORKING_MODEL = find_working_model()
    
    print(f"\n[!] АРХИВАРИУС: Анализирую {sender_name} ({len(new_messages)} новых строк)...")
    
    # 1. Достаем старую память из Supabase
    existing_memories = []
    memories_str = "База пуста."
    try:
        if supabase:
            existing_memories = supabase.table("memories").select("id, content").eq("user_id", user_id).execute().data
            if existing_memories:
                memories_str = "\n".join([f"[ID: {m['id']}] {m['content']}" for m in existing_memories])
    except Exception as e: print(f"[-] Ошибка выгрузки БД: {e}")

    full_history = "\n".join(new_messages)
    prompt_text = f"ТЕКУЩАЯ БАЗА ЗНАНИЙ:\n{memories_str}\n\nНОВЫЙ ДИАЛОГ:\n{full_history}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": ARCHIVIST_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        raw_answer = ""
        for p in r.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'text' in p: raw_answer += p['text'] + "\n"
            
        print(f"\n[!] ОТВЕТ АРХИВАРИУСА ДЛЯ {sender_name}:\n{raw_answer.strip()}\n")
        
        # 2. Парсим JSON и хирургически режем базу
        json_match = re.search(r'\{.*\}', raw_answer.strip(), re.DOTALL)
        if json_match and supabase:
            data = json.loads(json_match.group(0))
            
            # Удаляем старье
            to_delete = data.get("to_delete_ids", [])
            for d_id in to_delete:
                supabase.table("memories").delete().eq("id", d_id).execute()
                print(f"[-] Уничтожен старый/ошибочный вектор ID: {d_id}")
                
            # Добавляем новьё
            to_insert = data.get("to_insert", [])
            for fact in to_insert:
                threading.Thread(target=save_memory_to_supabase, args=(user_id, fact)).start()
                
        return True
    except Exception as e:
        print(f"[-] Ошибка Архивариуса для {sender_name}: {e}")
        return False

@app.on_message(filters.command("sleep", prefixes="!"))
async def global_sleep_command(client, message):
    await message.reply("*(закрывает глаза)* Ухожу в глубокий сон. Индексирую ВСЕ активные чаты...")
    
    processed_chats = 0
    # Проходимся по всем известным пользователям
    for u_id in list(USER_CARDS.keys()):
        msg_id, card_text, last_msg_id = await get_or_create_card(u_id, "Unknown")
        sender_name, _, history_lines = parse_card_info(card_text)
        
        new_messages = []
        latest_id = last_msg_id
        
        # Качаем историю до закладки
        try:
            async for msg in client.get_chat_history(u_id, limit=200):
                if msg.id <= last_msg_id: break
                if msg.id > latest_id: latest_id = msg.id
                
                # Фильтруем стикеры и команды!
                if msg.text and not msg.text.startswith("!"):
                    speaker = sender_name if msg.from_user and msg.from_user.id == u_id else "Ты"
                    new_messages.append(f"{speaker}: {msg.text}")
        except Exception: continue
            
        if new_messages:
            new_messages.reverse() # Хронологический порядок
            await asyncio.to_thread(run_archivist_for_user, u_id, sender_name, new_messages)
            await update_card_history(u_id, sender_name, history_lines, latest_id)
            processed_chats += 1
            await asyncio.sleep(5) # Пауза между юзерами для API
            
    await message.reply(f"*(открывает глаза)* Я проснулся. Обновлено чатов: {processed_chats}. Мозг кристально чист.")
# ==========================================

def ask_gemini(user_id, sender_name, user_text, card_text):
    global WORKING_MODEL
    if not WORKING_MODEL: WORKING_MODEL = find_working_model()
    if not WORKING_MODEL: return "Я сейчас немного туплю, отвечу позже.", []

    vector_context = get_relevant_memories(user_id, user_text)
    
    sender_name_parsed, last_msg_id, history_lines = parse_card_info(card_text)
    history_lines.append(f"Собеседник: {user_text}")
    if len(history_lines) > 8: history_lines = history_lines[-8:]
    dialogue_str = "\n".join(history_lines)
    
    prompt = f"Последний диалог:\n{dialogue_str}\n\n"
    if vector_context: prompt += f"ФАКТЫ ИЗ ДОЛГОВРЕМЕННОЙ ПАМЯТИ:\n{vector_context}\n\n"
    prompt += "Оцени сообщение. Если вопрос требует данных из интернета — СРАЗУ ВЫЗЫВАЙ ФУНКЦИЮ web_search."
    
    system_instruction = (
        "Ты — цифровой двойник реального парня. Характер: живой, ироничный, адекватный.\n"
        "СТИЛЬ РЕЧИ: Разговорный язык ('Бля', 'Крч', 'Ну'). Никаких робо-фраз.\n"
        "ФОРМАТ ОТВЕТА (ЕСЛИ НЕ ИСПОЛЬЗУЕШЬ ИНСТРУМЕНТ):\n"
        "Сначала напиши мысли в скобках.\n"
        "Затем на новой строке ТОЛЬКО саму реплику."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": GEMINI_TOOLS
    }
    
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'error' in r: return "Бля, гугл отвалился, сек.", history_lines
            
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
                
                follow_up_prompt = prompt + f"\n\n[СИСТЕМНОЕ СООБЩЕНИЕ: Результат инструмента:\n{tool_result}\n\nОпирайся на эти данные для ответа.]"
                payload2 = {
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"parts": [{"text": follow_up_prompt}]}]
                }
                r2 = requests.post(url, json=payload2, headers={'Content-Type': 'application/json'}).json()
                if 'error' in r2: return "Чет не могу переварить инфу из инета.", history_lines
                    
                raw_answer = ""
                for p in r2['candidates'][0]['content'].get('parts', []):
                    if 'text' in p: raw_answer += p['text'] + "\n"
            else:
                raw_answer = raw_text
            
            lines = [l.strip() for l in raw_answer.split('\n') if l.strip()]
            ans = ""
            for line in reversed(lines):
                if not line.startswith('(') and not line.endswith(')'):
                    if re.search(r'[А-Яа-яЁё]', line): ans = line; break
            if not ans and lines:
                for line in lines:
                    if not line.startswith('('): ans = line; break
                if not ans: ans = lines[-1]
                
            ans = re.sub(r'^[a-zA-Z0-9_ \-\.\?\!]+:\s*', '', ans).strip()
            ans = re.sub(r'^\d+\.\s*', '', ans).strip()
            ans = re.sub(r'^"|"$', '', ans).strip()
            if not ans: ans = "Чего?"

            # Отключаем автосохранение каждого пука! Теперь это делает Архивариус ночью.
            # threading.Thread(target=save_memory_to_supabase, args=(user_id, f"Собеседник сказал: {user_text} | Ты ответил: {ans}")).start()
            
            history_lines.append(f"Ты: {ans}")
            return ans, history_lines
    except Exception as e:
        print(f"[-] Ошибка API: {e}")
        
    fallback = "Чего?"
    history_lines.append(f"Ты: {fallback}")
    return fallback, history_lines

async def process_batch(client, message, user_id, sender_name):
    try: await asyncio.sleep(4)
    except asyncio.CancelledError: return
        
    msgs = PENDING_MESSAGES.pop(user_id, [])
    if not msgs: return
    combined_text = " | ".join(msgs)
    
    try: await app.send_chat_action(user_id, ChatAction.TYPING)
    except Exception: pass
    
    try:
        _, card_text, last_msg_id = await get_or_create_card(user_id, sender_name)
        reply_text, new_history = await asyncio.to_thread(ask_gemini, user_id, sender_name, combined_text, card_text)
        await update_card_history(user_id, sender_name, new_history, last_msg_id)
        if reply_text: await message.reply(reply_text)
    except Exception as e:
        await message.reply("Бля, у меня в мозгах че-то замкнуло, погоди.")

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    user_id = message.from_user.id
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    if user_id not in PENDING_MESSAGES: PENDING_MESSAGES[user_id] = []
    PENDING_MESSAGES[user_id].append(message.text)
    if user_id in PENDING_TASKS: PENDING_TASKS[user_id].cancel()
    PENDING_TASKS[user_id] = asyncio.create_task(process_batch(client, message, user_id, sender_name))

async def main():
    await app.start()
    init_supabase()
    await load_db()
    print("\n==========================================")
    print(" ЮЗЕРБОТ СТАРТОВАЛ (v7.0: ГЛОБАЛЬНЫЙ ФИЛЬТР) ")
    print("==========================================\n")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
