import os
import requests
import asyncio
import threading
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client, Client as SupabaseClient

# Костыль для новых версий Python
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction

# Микро-вебсервер
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

# Ключи
API_ID = int(os.environ.get("API_ID", "31001164"))
API_HASH = os.environ.get("API_HASH", "18ae94f76873c93be328527e858de657")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Инициализация Supabase
supabase: SupabaseClient = None

def init_supabase():
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n[!] ОШИБКА: SUPABASE_URL или SUPABASE_KEY не найдены в переменных Render!\n")
        return
    try:
        supabase = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())
        print("\n[+] SUPABASE УСПЕШНО ПОДКЛЮЧЕН!\n")
    except Exception as e:
        print(f"\n[-] ОШИБКА ПОДКЛЮЧЕНИЯ SUPABASE: {e}\n")

# Инвайт-ссылка канала-базы
CHANNEL_INVITE = "https://t.me/+VyP5UYDmzqkyZGZi"

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

WORKING_MODEL = None
CHANNEL_ID = None
USER_CARDS = {}

PENDING_MESSAGES = {}
PENDING_TASKS = {}

def find_working_model():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        for m in res['models']:
            model_name = m['name']
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": "hi"}]}]}
                r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
                if r.status_code == 200:
                    return model_name
    except Exception:
        pass
    return None

def get_embedding(text):
    """Генерация вектора (768 чисел) через Gemini"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }
    try:
        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'embedding' in r and 'values' in r['embedding']:
            return r['embedding']['values']
        else:
            print(f"[-] Ошибка формата эмбеддинга Gemini: {r}")
    except Exception as e:
        print(f"[-] Ошибка запроса эмбеддинга: {e}")
    return None

def save_memory_to_supabase(user_id, content):
    """Сохраняем факт переписки в векторную БД"""
    if not supabase:
        print("[-] Отмена записи: Supabase не инициализирован.")
        return
    vector = get_embedding(content)
    if not vector:
        print("[-] Отмена записи: Вектор не сгенерирован.")
        return
    try:
        res = supabase.table("memories").insert({
            "user_id": user_id,
            "content": content,
            "embedding": vector
        }).execute()
        print(f"[+] ВЕКТОРНАЯ ПАМЯТЬ УСПЕШНО СОХРАНЕНА В SUPABASE: '{content[:40]}...'")
    except Exception as e:
        print(f"[-] Ошибка записи в Supabase: {e}")

def get_relevant_memories(user_id, current_text):
    """Ищем 3 самых похожих по смыслу воспоминания из базы"""
    if not supabase: return ""
    vector = get_embedding(current_text)
    if not vector: return ""
    try:
        res = supabase.rpc("match_memories", {
            "query_embedding": vector,
            "match_threshold": 0.4,
            "match_count": 3,
            "p_user_id": user_id
        }).execute()
        
        if res.data and len(res.data) > 0:
            memories_list = [item['content'] for item in res.data]
            print(f"[!] ИЗВЛЕЧЕНО ВЕКТОРНЫХ ВОСПОМИНАНИЙ: {len(memories_list)}")
            return "\n".join(memories_list)
    except Exception as e:
        print(f"[-] Ошибка поиска векторов в Supabase: {e}")
    return ""

async def load_db():
    global CHANNEL_ID, USER_CARDS
    try:
        print(f"[~] Резолвлю канал через инвайт-ссылку...")
        chat = await app.get_chat(CHANNEL_INVITE)
        CHANNEL_ID = chat.id
        print(f"[+] Успешно! Канал '{chat.title}' привязан. ID: {CHANNEL_ID}")
        
        async for message in app.get_chat_history(CHANNEL_ID, limit=200):
            if message.text:
                match = re.search(r'\[USER_ID:\s*(-?\d+)\]', message.text)
                if match:
                    uid = int(match.group(1))
                    if uid not in USER_CARDS:
                        USER_CARDS[uid] = message.id
        print(f"[!] Канал загружен. Найдено карточек: {len(USER_CARDS)}")
    except Exception as e:
        print(f"\n[-] КРИТИЧЕСКАЯ ОШИБКА РЕЗОЛВА КАНАЛА: {e}\n")

async def get_or_create_card(user_id, sender_name):
    if not CHANNEL_ID: return None, ""
    if user_id not in USER_CARDS:
        initial_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n"
        try:
            sent = await app.send_message(CHANNEL_ID, initial_text)
            USER_CARDS[user_id] = sent.id
            return sent.id, initial_text
        except Exception:
            return None, initial_text
    else:
        msg_id = USER_CARDS[user_id]
        try:
            msg = await app.get_messages(CHANNEL_ID, msg_id)
            if msg and msg.text:
                return msg_id, msg.text
        except Exception:
            pass
        return None, ""

async def update_card_history(user_id, sender_name, history_lines):
    if not CHANNEL_ID: return
    msg_id, _ = await get_or_create_card(user_id, sender_name)
    if not msg_id: return
    
    history_str = "\n".join(history_lines)
    full_text = f"[USER_ID: {user_id}]\nИмя: {sender_name}\nИстория:\n{history_str}"
    if len(full_text) > 4000:
        full_text = full_text[-4000:]
    try:
        await app.edit_message_text(CHANNEL_ID, msg_id, full_text)
    except Exception:
        pass

def parse_history_from_text(card_text):
    lines = card_text.split('\n')
    history_lines = []
    capture = False
    for line in lines:
        if line.startswith("История:"):
            capture = True
            continue
        if capture and line.strip():
            history_lines.append(line.strip())
    return history_lines

def ask_gemini(user_id, sender_name, user_text, card_text):
    global WORKING_MODEL
    if not WORKING_MODEL:
        WORKING_MODEL = find_working_model()
    if not WORKING_MODEL:
        return "Я сейчас немного туплю, отвечу позже.", []
    
    # 1. Запрашиваем смысловые воспоминания из Supabase
    vector_context = get_relevant_memories(user_id, user_text)
    
    # 2. Берем последние пару сообщений из карточки
    history_lines = parse_history_from_text(card_text)
    history_lines.append(f"Собеседник: {user_text}")
    if len(history_lines) > 8:
        history_lines = history_lines[-8:]
        
    dialogue_str = "\n".join(history_lines)
    
    prompt = f"Последний диалог:\n{dialogue_str}\n\n"
    if vector_context:
        prompt += f"ФАКТЫ ИЗ ДОЛГОВРЕМЕННОЙ ПАМЯТИ ОБ ЭТОМ ЧЕЛОВЕКЕ:\n{vector_context}\n\n"
        
    prompt += "Оцени последнее сообщение, учитывай долгосрочные факты (если есть) и напиши ответную реплику от первого лица."
    
    system_instruction = (
        "Ты — цифровой двойник реального парня. Твой характер: живой, ироничный, адекватный, но со стержнем.\n\n"
        "ПРАВИЛА ПОВЕДЕНИЯ:\n"
        "1. ЗЕРКАЛО И ДИНАМИКА: Отвечай адекватно тону собеседника. Смещай гнев на милость, если собеседник пишет нормально.\n"
        "2. ИСПОЛЬЗУЙ ВЕКТОРНУЮ ПАМЯТЬ: Если в блоке фактов есть нужная инфа — опирайся на нее естественно, будто реально помнишь.\n"
        "3. Если ржет — подкалывай. Если грубит — ставь на место.\n\n"
        "СТИЛЬ РЕЧИ:\n"
        "- Живой разговорный язык, междометия ('Бля', 'Крч', 'Ну', 'Ахуеть').\n"
        "- Никаких робо-фраз.\n\n"
        "ФОРМАТ ОТВЕТА:\n"
        "Сначала напиши свои мысли в скобках (например: '(вспоминаю прошлый базар)').\n"
        "Сразу после скобок на новой строке напиши ТОЛЬКО саму реплику на русском языке."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'candidates' in response and len(response['candidates']) > 0:
            raw_answer = response['candidates'][0]['content']['parts'][0]['text']
            
            lines = [l.strip() for l in raw_answer.split('\n') if l.strip()]
            ans = ""
            for line in reversed(lines):
                if not line.startswith('(') and not line.endswith(')'):
                    if re.search(r'[А-Яа-яЁё]', line):
                        ans = line
                        break
            
            if not ans and lines:
                for line in lines:
                    if not line.startswith('('):
                        ans = line
                        break
                if not ans:
                    ans = lines[-1]
                
            ans = re.sub(r'^[a-zA-Z0-9_ \-\.\?\!]+:\s*', '', ans).strip()
            ans = re.sub(r'^\d+\.\s*', '', ans).strip()
            ans = re.sub(r'^"|"$', '', ans).strip()
            
            if not ans:
                ans = "Чего?"

            # Сохраняем новую пару реплик в векторную память в фоновом потоке
            threading.Thread(target=save_memory_to_supabase, args=(user_id, f"Собеседник сказал: {user_text} | Ты ответил: {ans}")).start()

            history_lines.append(f"Ты: {ans}")
            return ans, history_lines
    except Exception as e:
        print(f"[-] Ошибка API Gemini: {e}")
        
    fallback = "Чего?"
    history_lines.append(f"Ты: {fallback}")
    return fallback, history_lines

async def process_batch(client, message, user_id, sender_name):
    try:
        await asyncio.sleep(4)
    except asyncio.CancelledError:
        return
        
    msgs = PENDING_MESSAGES.pop(user_id, [])
    if not msgs: return
    
    combined_text = " | ".join(msgs)
    
    try:
        await app.send_chat_action(user_id, ChatAction.TYPING)
    except Exception:
        pass
    
    try:
        _, card_text = await get_or_create_card(user_id, sender_name)
        reply_text, new_history = await asyncio.to_thread(ask_gemini, user_id, sender_name, combined_text, card_text)
        await update_card_history(user_id, sender_name, new_history)
        
        if reply_text:
            await message.reply(reply_text)
    except Exception as e:
        print(f"[-] Ошибка в process_batch: {e}")
        await message.reply("Бля, у меня в мозгах че-то замкнуло, погоди.")

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    user_id = message.from_user.id
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    
    if user_id not in PENDING_MESSAGES:
        PENDING_MESSAGES[user_id] = []
    PENDING_MESSAGES[user_id].append(message.text)
    
    if user_id in PENDING_TASKS:
        PENDING_TASKS[user_id].cancel()
        
    PENDING_TASKS[user_id] = asyncio.create_task(process_batch(client, message, user_id, sender_name))

async def main():
    await app.start()
    init_supabase()  # Явная инициализация Supabase при старте!
    await load_db()
    print("\n==========================================")
    print(" ЮЗЕРБОТ СТАРТОВАЛ (v5.1: ДИАГНОСТИКА ВЕКТОРОВ) ")
    print("==========================================\n")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
