import os
import gc
import sys
import time
import uuid
import base64
import re
import json
import ssl
import socket
import struct
import hashlib
import random
import html
import tarfile
import tempfile
import subprocess
import urllib.parse
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# =====================================================================
# 1. ИНИЦИАЛИЗАЦИЯ ОКРУЖЕНИЯ И НОВЫХ КЛЮЧЕЙ (СТАРЫЙ ТОКЕН СБРОШЕН)
# =====================================================================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if not RENDER_HOSTNAME and RENDER_EXTERNAL_URL:
    RENDER_HOSTNAME = urllib.parse.urlsplit(RENDER_EXTERNAL_URL).hostname or ""

_SEED = f"{GITHUB_TOKEN}:{GITHUB_REPO}:{TG_TOKEN}:great_vpn_v5_verified"
SUB_TOKEN = os.environ.get("SUB_TOKEN", hashlib.sha256(_SEED.encode()).hexdigest()[:16])
WS_SECRET_PATH = f"/ws-{SUB_TOKEN}"
VLESS_UUID = str(uuid.UUID(bytes=hashlib.md5(_SEED.encode()).digest()))
VLESS_UUID_BYTES = uuid.UUID(VLESS_UUID).bytes

SINGBOX_BIN = "/tmp/sing-box"
VPN_LOCK = threading.Lock()
STATE_LOCK = threading.Lock()
VPN_REFRESH_EVENT = threading.Event()
HARVEST_RUNNING = False

GH_SESSION = requests.Session()
if GITHUB_TOKEN:
    GH_SESSION.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "GreatVPN-Verifier/5.0"
    })

TG_SESSION = requests.Session()
HTTP_SCRAPER = requests.Session()
HTTP_SCRAPER.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36"
})

GITHUB_BASE = "https://api.github.com/repos/"

# =====================================================================
# 2. ОТКРЫТЫЕ АГРЕГАТОРЫ И ФИЛЬТРЫ ШАБЛОНОВ
# =====================================================================
PUBLIC_AGGREGATORS = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/hy2.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/normal/reality",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/normal/vless",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/normal/trojan",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/reality",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
]

DUMMY_HOSTS = {
    "example.com", "example.org", "example.net", "localhost", "127.0.0.1",
    "0.0.0.0", "yourdomain.com", "domain.com", "server.com", "host"
}

DUMMY_SECRETS = {
    "00000000-0000-0000-0000-000000000000",
    "11111111-1111-1111-1111-111111111111",
    "uuid", "your-uuid", "password", "your-password", "changeme"
}

DEFAULT_RU_WHITELIST_SNI = [
    "st.ozone.ru", "stats.vk-portal.net", "avatars.mds.yandex.net",
    "sba.yandex.net", "dl.google.com", "www.microsoft.com", "itunes.apple.com"
]

VPN_STATE = {
    "last_updated": "Инициализация ядра...",
    "singbox_ready": False,
    "verified_nodes": [],
    "raw_uris": [],
    "sub_base64": "",
    "singbox_json": "",
    "custom_sni": list(DEFAULT_RU_WHITELIST_SNI),
    "relay_connections": 0,
    "relay_bytes": 0,
    "tested_total": 0
}


# =====================================================================
# 3. УСТАНОВКА БОЕВОГО ЯДРА SING-BOX ДЛЯ РЕАЛЬНОЙ ПРОВЕРКИ ТРАФИКА
# =====================================================================
def ensure_singbox_binary() -> bool:
    """Скачивает официальный релиз sing-box для Linux amd64 в /tmp для реального прогона трафика."""
    if os.path.isfile(SINGBOX_BIN) and os.access(SINGBOX_BIN, os.X_OK):
        with VPN_LOCK:
            VPN_STATE["singbox_ready"] = True
        return True

    try:
        r = HTTP_SCRAPER.get("https://api.github.com/repos/SagerNet/sing-box/releases/latest", timeout=10)
        if r.status_code != 200:
            return False
        assets = r.json().get("assets", [])
        dl_url = next(
            (a["browser_download_url"] for a in assets if "linux-amd64.tar.gz" in a.get("name", "") and "musl" not in a.get("name", "")),
            ""
        )
        if not dl_url:
            return False

        tgz_path = "/tmp/sb.tar.gz"
        with HTTP_SCRAPER.get(dl_url, stream=True, timeout=40) as resp:
            resp.raise_for_status()
            with open(tgz_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

        with tarfile.open(tgz_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("/sing-box") or member.name == "sing-box":
                    extracted = tar.extractfile(member)
                    if extracted:
                        with open(SINGBOX_BIN, "wb") as out_f:
                            out_f.write(extracted.read())
                        os.chmod(SINGBOX_BIN, 0o755)
                        break

        if os.path.exists(tgz_path):
            os.remove(tgz_path)

        ready = os.path.isfile(SINGBOX_BIN) and os.access(SINGBOX_BIN, os.X_OK)
        with VPN_LOCK:
            VPN_STATE["singbox_ready"] = ready
        return ready
    except Exception as e:
        print(f"[!] Ошибка загрузки sing-box: {e}")
        return False


# =====================================================================
# 4. ВСТРОЕННЫЙ ЛИЧНЫЙ VLESS-OVER-WEBSOCKET НА RENDER
# =====================================================================
def get_self_vless_uri(custom_host: str = "") -> str:
    host = custom_host or RENDER_HOSTNAME or "my-userbot-3j04.onrender.com"
    params = urllib.parse.urlencode({
        "encryption": "none",
        "security": "tls",
        "sni": host,
        "fp": "chrome",
        "type": "ws",
        "host": host,
        "path": WS_SECRET_PATH,
        "alpn": "http/1.1"
    })
    return f"vless://{VLESS_UUID}@{host}:443?{params}#{urllib.parse.quote('👑 МОЙ ЛИЧНЫЙ RENDER VLESS')}"


def _ws_unmask(payload: bytes, mask_key: bytes) -> bytes:
    n = len(payload)
    if n == 0:
        return b""
    repeated = (mask_key * ((n // 4) + 1))[:n]
    return (int.from_bytes(payload, "big") ^ int.from_bytes(repeated, "big")).to_bytes(n, "big")


def _ws_build_frame(data: bytes, opcode: int = 0x02) -> bytes:
    n = len(data)
    header = bytearray([0x80 | opcode])
    if n < 126:
        header.append(n)
    elif n < 65536:
        header.append(126)
        header.extend(struct.pack("!H", n))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", n))
    return bytes(header) + data


def _recv_exact_sock(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError()
        buf.extend(chunk)
    return bytes(buf)


def _ws_read_frame_sock(sock: socket.socket) -> tuple:
    b1, b2 = _recv_exact_sock(sock, 2)
    opcode = b1 & 0x0F
    masked = (b2 & 0x80) != 0
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact_sock(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact_sock(sock, 8))[0]
    if length > 2 * 1024 * 1024:
        raise ValueError("Frame too large")
    mask_key = _recv_exact_sock(sock, 4) if masked else b""
    payload = _recv_exact_sock(sock, length)
    if masked:
        payload = _ws_unmask(payload, mask_key)
    return opcode, payload


def handle_vless_websocket_tunnel(handler: BaseHTTPRequestHandler):
    ws_key = handler.headers.get("Sec-WebSocket-Key", "").strip()
    if not ws_key:
        return
    accept_val = base64.b64encode(
        hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
    ).decode("ascii")

    client_sock = handler.connection
    client_sock.settimeout(30)
    try:
        client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception:
        pass

    client_sock.sendall(
        ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
         f"Sec-WebSocket-Accept: {accept_val}\r\n\r\n").encode("ascii")
    )

    write_lock = threading.Lock()
    target_sock = None
    stop_event = threading.Event()

    def _ws_send(data: bytes, opcode: int = 0x02):
        with write_lock:
            client_sock.sendall(_ws_build_frame(data, opcode=opcode))

    try:
        first_payload = b""
        while not first_payload:
            op, pl = _ws_read_frame_sock(client_sock)
            if op == 0x08:
                return
            if op == 0x09:
                _ws_send(pl, opcode=0x0A)
                continue
            if op in (0x01, 0x02, 0x00) and pl:
                first_payload = pl

        if len(first_payload) < 24 or first_payload[0] != 0 or first_payload[1:17] != VLESS_UUID_BYTES:
            return
        addons_len = first_payload[17]
        pos = 18 + addons_len
        if len(first_payload) < pos + 4 or first_payload[pos] != 1:
            return
        dst_port = struct.unpack("!H", first_payload[pos + 1:pos + 3])[0]
        atyp = first_payload[pos + 3]
        pos += 4

        if atyp == 1:
            dst_host, pos = socket.inet_ntoa(first_payload[pos:pos + 4]), pos + 4
        elif atyp == 2:
            dlen = first_payload[pos]
            dst_host, pos = first_payload[pos + 1:pos + 1 + dlen].decode("utf-8", errors="ignore"), pos + 1 + dlen
        elif atyp == 3:
            dst_host, pos = socket.inet_ntop(socket.AF_INET6, first_payload[pos:pos + 16]), pos + 16
        else:
            return

        initial_tcp_data = first_payload[pos:]
        target_sock = socket.create_connection((dst_host, dst_port), timeout=10)
        target_sock.settimeout(30)

        with VPN_LOCK:
            VPN_STATE["relay_connections"] += 1
        if initial_tcp_data:
            target_sock.sendall(initial_tcp_data)
            with VPN_LOCK:
                VPN_STATE["relay_bytes"] += len(initial_tcp_data)

        def _pump_target_to_ws():
            first = True
            try:
                while not stop_event.is_set():
                    data = target_sock.recv(16384)
                    if not data:
                        break
                    if first:
                        data = b"\x00\x00" + data
                        first = False
                    _ws_send(data, opcode=0x02)
                    with VPN_LOCK:
                        VPN_STATE["relay_bytes"] += len(data)
            except Exception:
                pass
            finally:
                stop_event.set()

        threading.Thread(target=_pump_target_to_ws, daemon=True).start()
        while not stop_event.is_set():
            op, pl = _ws_read_frame_sock(client_sock)
            if op == 0x08:
                break
            elif op == 0x09:
                _ws_send(pl, opcode=0x0A)
            elif op in (0x01, 0x02, 0x00) and pl:
                target_sock.sendall(pl)
                with VPN_LOCK:
                    VPN_STATE["relay_bytes"] += len(pl)
    except Exception:
        pass
    finally:
        stop_event.set()
        if target_sock:
            try:
                target_sock.close()
            except Exception:
                pass


# =====================================================================
# 5. ПАРСЕР И РЕАЛЬНЫЙ ПРОГОН ТРАФИКА ЧЕРЕЗ SING-BOX
# =====================================================================
def _fetch_limited_lines(url: str, max_bytes: int = 300_000) -> list:
    try:
        with HTTP_SCRAPER.get(url, timeout=8, stream=True) as r:
            if r.status_code != 200:
                return []
            buf = bytearray()
            for chunk in r.iter_content(chunk_size=16384):
                if chunk:
                    buf.extend(chunk)
                    if len(buf) >= max_bytes:
                        break
        text = bytes(buf).decode("utf-8", errors="ignore").strip()
        if "://" not in text[:120]:
            try:
                padded = text + "=" * ((4 - len(text) % 4) % 4)
                text = base64.b64decode(padded).decode("utf-8", errors="ignore")
            except Exception:
                pass
        return [
            l.strip() for l in text.splitlines()
            if any(l.strip().startswith(p) for p in ("vless://", "trojan://", "hysteria2://", "hy2://"))
        ]
    except Exception:
        return []


def parse_proxy_uri(uri: str) -> dict:
    try:
        parsed = urllib.parse.urlsplit(uri)
        scheme = parsed.scheme.lower()
        if scheme not in ("vless", "trojan", "hysteria2", "hy2") or "@" not in parsed.netloc:
            return {}
        userinfo, hostport = parsed.netloc.rsplit("@", 1)
        userinfo = urllib.parse.unquote(userinfo).strip()

        if not userinfo or userinfo.lower() in DUMMY_SECRETS:
            return {}
        if hostport.startswith("["):
            return {}

        if ":" in hostport:
            host, port_str = hostport.rsplit(":", 1)
            port = int(port_str)
        else:
            host, port = hostport, 443

        host = host.strip().lower()
        if not host or host in DUMMY_HOSTS or host.endswith(".example.com") or port <= 0 or port > 65535:
            return {}

        qs = dict(urllib.parse.parse_qsl(parsed.query))
        security = qs.get("security", "tls" if scheme in ("trojan", "hysteria2", "hy2") else "none").lower()
        net_type = qs.get("type", "tcp").lower()
        sni = (qs.get("sni") or qs.get("peer") or qs.get("host") or host).strip()

        if sni.lower() in DUMMY_HOSTS:
            return {}
        if scheme == "vless" and security not in ("reality", "tls"):
            return {}
        if scheme == "vless" and security == "tls" and net_type == "tcp":
            return {}
        if security == "reality" and len(qs.get("pbk", "")) < 20:
            return {}

        return {
            "scheme": "hysteria2" if scheme == "hy2" else scheme,
            "uuid_or_pass": userinfo,
            "host": host,
            "port": port,
            "params": qs,
            "security": security,
            "type": net_type,
            "sni": sni
        }
    except Exception:
        return {}


def _node_to_singbox_outbound(node: dict, tag: str) -> dict:
    p = node["params"]
    scheme = node["scheme"]
    if scheme == "vless":
        ob = {
            "type": "vless",
            "tag": tag,
            "server": node["host"],
            "server_port": node["port"],
            "uuid": node["uuid_or_pass"],
            "tls": {
                "enabled": True,
                "server_name": p.get("sni", node["sni"]),
                "insecure": True,
                "utls": {"enabled": True, "fingerprint": "chrome"}
            }
        }
        if p.get("flow"):
            ob["flow"] = p["flow"]
        if node["security"] == "reality":
            ob["tls"]["reality"] = {
                "enabled": True,
                "public_key": p.get("pbk", ""),
                "short_id": p.get("sid", "")
            }
        if node["type"] == "ws":
            ob["transport"] = {
                "type": "ws",
                "path": p.get("path", "/"),
                "headers": {"Host": p.get("host", p.get("sni", node["host"]))}
            }
        elif node["type"] == "grpc":
            ob["transport"] = {"type": "grpc", "service_name": p.get("serviceName", "")}
        return ob

    if scheme == "trojan":
        ob = {
            "type": "trojan",
            "tag": tag,
            "server": node["host"],
            "server_port": node["port"],
            "password": node["uuid_or_pass"],
            "tls": {
                "enabled": True,
                "server_name": p.get("sni", node["sni"]),
                "insecure": True,
                "utls": {"enabled": True, "fingerprint": "chrome"}
            }
        }
        if node["type"] == "ws":
            ob["transport"] = {
                "type": "ws",
                "path": p.get("path", "/"),
                "headers": {"Host": p.get("host", p.get("sni", node["host"]))}
            }
        return ob

    if scheme == "hysteria2":
        ob = {
            "type": "hysteria2",
            "tag": tag,
            "server": node["host"],
            "server_port": node["port"],
            "password": node["uuid_or_pass"],
            "tls": {
                "enabled": True,
                "server_name": p.get("sni", node["sni"]),
                "insecure": True
            }
        }
        if p.get("obfs") == "salamander" and p.get("obfs-password"):
            ob["obfs"] = {"type": "salamander", "password": p["obfs-password"]}
        return ob
    return {}


def _precheck_tcp_port(node: dict) -> bool:
    """Быстрый отсев закрытых TCP-портов перед запуском sing-box (Hysteria2 пропускаем сразу в sing-box)."""
    if node["scheme"] == "hysteria2":
        return True
    try:
        with socket.create_connection((node["host"], node["port"]), timeout=1.5):
            return True
    except Exception:
        return False


def verify_batch_with_singbox(candidates: list, whitelist_snis: list) -> list:
    """
    Запускает один общий экземпляр sing-box с индивидуальным локальным HTTP-прокси портом на каждый узел
    и делает реальный запрос http://www.gstatic.com/generate_204 сквозь каждый узел.
    """
    if not candidates or not ensure_singbox_binary():
        return []

    base_port = random.randint(22000, 35000)
    inbounds = []
    outbounds = []
    rules = []
    port_map = {}

    for idx, node in enumerate(candidates):
        local_port = base_port + idx
        in_tag = f"in_{idx}"
        out_tag = f"out_{idx}"
        ob = _node_to_singbox_outbound(node, out_tag)
        if not ob:
            continue

        inbounds.append({
            "type": "http",
            "tag": in_tag,
            "listen": "127.0.0.1",
            "listen_port": local_port
        })
        outbounds.append(ob)
        rules.append({"inbound": [in_tag], "outbound": out_tag})
        port_map[local_port] = node

    if not outbounds:
        return []

    outbounds.append({"type": "direct", "tag": "direct"})
    config = {
        "log": {"level": "error"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "route": {"rules": rules, "final": "direct"}
    }

    cfg_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    try:
        json.dump(config, cfg_file)
        cfg_file.close()

        proc = subprocess.Popen(
            [SINGBOX_BIN, "run", "-c", cfg_file.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.5)  # Даём sing-box поднять локальные порты

        def _probe_port(item):
            lport, node = item
            proxies = {
                "http": f"http://127.0.0.1:{lport}",
                "https": f"http://127.0.0.1:{lport}"
            }
            t0 = time.time()
            try:
                resp = requests.get("http://www.gstatic.com/generate_204", proxies=proxies, timeout=4.5)
                if resp.status_code in (200, 204):
                    real_ms = int((time.time() - t0) * 1000)
                    params = dict(node["params"])
                    params["fp"] = "chrome"
                    if node["security"] == "reality" and not params.get("sni"):
                        params["sni"] = random.choice(whitelist_snis)

                    badge = "REALITY" if node["security"] == "reality" else (
                        "HY2" if node["scheme"] == "hysteria2" else node["scheme"].upper()
                    )
                    tag = f"✅ [{badge}] {node['host'][:16]}:{node['port']} ({real_ms}ms)"
                    q_str = urllib.parse.urlencode(params, safe=":,/")
                    mutated_uri = f"{node['scheme']}://{urllib.parse.quote(node['uuid_or_pass'])}@{node['host']}:{node['port']}?{q_str}#{urllib.parse.quote(tag)}"

                    out = dict(node)
                    out.update({
                        "latency_ms": real_ms,
                        "tag": tag,
                        "mutated_uri": mutated_uri
                    })
                    return out
            except Exception:
                pass
            return {}

        verified = []
        with ThreadPoolExecutor(max_workers=20) as pool:
            for res in pool.map(_probe_port, port_map.items()):
                if res:
                    verified.append(res)

        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

        return verified
    finally:
        if os.path.exists(cfg_file.name):
            os.remove(cfg_file.name)


def build_singbox_profile(nodes: list) -> dict:
    outbounds = []
    outbound_tags = []

    if RENDER_HOSTNAME:
        self_tag = f"👑 МОЙ RENDER VLESS ({RENDER_HOSTNAME})"
        outbounds.append({
            "type": "vless",
            "tag": self_tag,
            "server": RENDER_HOSTNAME,
            "server_port": 443,
            "uuid": VLESS_UUID,
            "tls": {"enabled": True, "server_name": RENDER_HOSTNAME, "utls": {"enabled": True, "fingerprint": "chrome"}},
            "transport": {"type": "ws", "path": WS_SECRET_PATH, "headers": {"Host": RENDER_HOSTNAME}}
        })
        outbound_tags.append(self_tag)

    for idx, n in enumerate(nodes[:25]):
        tag = f"{n['tag']} #{idx + 1}"
        ob = _node_to_singbox_outbound(n, tag)
        if ob:
            outbounds.append(ob)
            outbound_tags.append(tag)

    if not outbound_tags:
        outbound_tags = ["direct"]

    header = [
        {"type": "selector", "tag": "🚀 ВЕЛИКИЙ ВПН (Проверено)", "outbounds": ["⚡ АВТО-ПИНГ"] + outbound_tags + ["direct"], "default": "⚡ АВТО-ПИНГ"},
        {"type": "urltest", "tag": "⚡ АВТО-ПИНГ", "outbounds": outbound_tags, "url": "https://www.gstatic.com/generate_204", "interval": "2m", "tolerance": 60}
    ]
    tail = [{"type": "direct", "tag": "direct"}, {"type": "block", "tag": "block"}, {"type": "dns", "tag": "dns-out"}]

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "dns-remote", "address": "https://1.1.1.1/dns-query", "address_resolver": "dns-direct", "detour": "🚀 ВЕЛИКИЙ ВПН (Проверено)"},
                {"tag": "dns-direct", "address": "77.88.8.8", "detour": "direct"}
            ],
            "rules": [{"domain_suffix": [".ru", ".su", ".xn--p1ai"], "server": "dns-direct"}],
            "final": "dns-remote"
        },
        "inbounds": [{"type": "tun", "tag": "tun-in", "inet4_address": "172.19.0.1/30", "mtu": 1400, "auto_route": True, "strict_route": True, "sniff": True}],
        "outbounds": header + outbounds + tail,
        "route": {
            "auto_detect_interface": True,
            "rules": [
                {"protocol": "dns", "outbound": "dns-out"},
                {"ip_is_private": True, "outbound": "direct"},
                {"domain_suffix": [".ru", ".su", ".xn--p1ai", "yandex.net", "vk.com", "userapi.com", "ozon.ru", "wb.ru", "sberbank.ru", "tbank.ru", "gosuslugi.ru"], "outbound": "direct"}
            ],
            "final": "🚀 ВЕЛИКИЙ ВПН (Проверено)"
        }
    }


def push_vpn_backup_to_github(files_dict: dict):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return
    try:
        ref_url = f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main"
        r = GH_SESSION.get(ref_url, timeout=10)
        if r.status_code != 200:
            return
        head_sha = r.json()["object"]["sha"]
        base_tree = GH_SESSION.get(f"{GITHUB_BASE}{GITHUB_REPO}/git/commits/{head_sha}", timeout=10).json()["tree"]["sha"]
        tree_items = [{"path": p, "mode": "100644", "type": "blob", "content": c} for p, c in files_dict.items()]
        new_tree = GH_SESSION.post(f"{GITHUB_BASE}{GITHUB_REPO}/git/trees", json={"base_tree": base_tree, "tree": tree_items}, timeout=12).json()["sha"]
        new_commit = GH_SESSION.post(
            f"{GITHUB_BASE}{GITHUB_REPO}/git/commits",
            json={"message": "🛡️ Обновление реально проверенных нод [skip ci]", "tree": new_tree, "parents": [head_sha]},
            timeout=10
        ).json()["sha"]
        GH_SESSION.patch(ref_url, json={"sha": new_commit}, timeout=10)
    except Exception:
        pass


def execute_verified_harvest(notify_tg: bool = False):
    global HARVEST_RUNNING
    with STATE_LOCK:
        if HARVEST_RUNNING:
            return
        HARVEST_RUNNING = True

    try:
        ensure_singbox_binary()
        with VPN_LOCK:
            snis = list(VPN_STATE["custom_sni"])

        feeds = random.sample(PUBLIC_AGGREGATORS, min(7, len(PUBLIC_AGGREGATORS)))
        parsed_map = {}

        with ThreadPoolExecutor(max_workers=6) as pool:
            for lines in pool.map(_fetch_limited_lines, feeds):
                random.shuffle(lines)
                for uri in lines[:70]:
                    p = parse_proxy_uri(uri)
                    if p:
                        parsed_map[f"{p['host']}:{p['port']}"] = p
                    if len(parsed_map) >= 180:
                        break
                if len(parsed_map) >= 180:
                    break

        # 1. Быстрый TCP-фильтр
        tcp_alive = []
        with ThreadPoolExecutor(max_workers=25) as pool:
            futures = {pool.submit(_precheck_tcp_port, n): n for n in parsed_map.values()}
            for fut in as_completed(futures):
                if fut.result():
                    tcp_alive.append(futures[fut])
                if len(tcp_alive) >= 80:
                    break

        # 2. Реальный прогон HTTP generate_204 через sing-box батчами по 40 штук
        verified = []
        for i in range(0, len(tcp_alive), 40):
            batch = tcp_alive[i:i + 40]
            verified.extend(verify_batch_with_singbox(batch, snis))

        verified.sort(key=lambda x: x["latency_ms"])
        top_nodes = verified[:25]

        uris = []
        if RENDER_HOSTNAME:
            uris.append(get_self_vless_uri(RENDER_HOSTNAME))
        uris.extend(n["mutated_uri"] for n in top_nodes)

        sub_b64 = base64.b64encode("\n".join(uris).encode("utf-8")).decode("ascii")
        sb_json = json.dumps(build_singbox_profile(top_nodes), indent=2, ensure_ascii=False)
        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

        with VPN_LOCK:
            VPN_STATE["last_updated"] = now_str
            VPN_STATE["verified_nodes"] = top_nodes
            VPN_STATE["raw_uris"] = uris
            VPN_STATE["sub_base64"] = sub_b64
            VPN_STATE["singbox_json"] = sb_json
            VPN_STATE["tested_total"] = len(tcp_alive)

        push_vpn_backup_to_github({
            "vpn/sub_base64.txt": sub_b64,
            "vpn/sub_raw.txt": "\n".join(uris),
            "vpn/singbox_verified.json": sb_json
        })

        if notify_tg:
            best = f"{top_nodes[0]['latency_ms']} ms" if top_nodes else "нет"
            send_tg(
                f"✅ <b>Реальная проверка через Sing-box завершена!</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"🧪 <b>Прогнано через туннель:</b> {len(tcp_alive)} узлов\n"
                f"🟢 <b>Реально открывают интернет:</b> {len(top_nodes)}\n"
                f"⚡ <b>Лучший реальный отклик:</b> {best}\n\n"
                f"Жми <code>/vpn</code> за свежей подпиской."
            )
    finally:
        with STATE_LOCK:
            HARVEST_RUNNING = False
        gc.collect()


def run_harvester_daemon():
    time.sleep(3)
    while True:
        try:
            execute_verified_harvest(notify_tg=False)
        except Exception as e:
            print(f"[!] Ошибка цикла проверки: {e}")
        VPN_REFRESH_EVENT.wait(timeout=1800)
        VPN_REFRESH_EVENT.clear()


# =====================================================================
# 6. HTTP СЕРВЕР (ЛИЧНЫЙ VLESS WS + РАЗДАЧА ПРОВЕРЕННЫХ ПОДПИСОК)
# =====================================================================
class GreatVPNHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    rbufsize = 0

    def log_message(self, format, *args):
        pass

    def _send_text(self, code: int, body: str, content_type: str = "text/plain; charset=utf-8", extra_headers: dict = None):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(encoded)
        self.wfile.flush()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()
        self.wfile.flush()

    def do_GET(self):
        global RENDER_HOSTNAME
        host_hdr = self.headers.get("Host", "").split(":")[0].strip()
        if host_hdr and not RENDER_HOSTNAME and "onrender.com" in host_hdr:
            RENDER_HOSTNAME = host_hdr
        parsed = urllib.parse.urlsplit(self.path)

        if parsed.path == WS_SECRET_PATH:
            handle_vless_websocket_tunnel(self)
            self.close_connection = True
            return

        qs = dict(urllib.parse.parse_qsl(parsed.query))
        if parsed.path in ("/", "/health", "/ping"):
            self._send_text(200, "GreatVPN Verifier Operational")
            return

        if parsed.path in ("/sub", "/raw", "/singbox"):
            if qs.get("token", "") != SUB_TOKEN:
                self._send_text(403, "Forbidden")
                return

            with VPN_LOCK:
                sub_b64 = VPN_STATE["sub_base64"]
                raw_uris = "\n".join(VPN_STATE["raw_uris"])
                sb_json = VPN_STATE["singbox_json"]

            sub_headers = {"Profile-Title": base64.b64encode("🛡️ GreatVPN Verified".encode()).decode()}
            if parsed.path == "/sub":
                self._send_text(200, sub_b64 or base64.b64encode(get_self_vless_uri(RENDER_HOSTNAME).encode()).decode(), extra_headers=sub_headers)
            elif parsed.path == "/raw":
                self._send_text(200, raw_uris or get_self_vless_uri(), extra_headers=sub_headers)
            elif parsed.path == "/singbox":
                self._send_text(200, sb_json or "{}", content_type="application/json; charset=utf-8", extra_headers=sub_headers)
            return

        self._send_text(404, "Not Found")


class PooledThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = PooledThreadingHTTPServer(('0.0.0.0', port), GreatVPNHTTPHandler)
    server.serve_forever()


threading.Thread(target=run_http_server, daemon=True).start()
threading.Thread(target=run_harvester_daemon, daemon=True).start()


# =====================================================================
# 7. TELEGRAM ИНТЕРФЕЙС
# =====================================================================
def send_tg(text: str, buttons: list = None, keyboard: bool = False):
    if not TG_TOKEN or not TG_ADMIN_ID:
        return
    payload = {"chat_id": TG_ADMIN_ID, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": True}
    if keyboard:
        payload["reply_markup"] = json.dumps({"keyboard": [["🛡️ /vpn", "👑 /myvless"], ["🔄 /check", "📊 /ping"]], "resize_keyboard": True})
    elif buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    try:
        TG_SESSION.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json=payload, timeout=8)
    except Exception:
        pass


def set_tg_commands():
    if not TG_TOKEN:
        return
    commands = [
        {"command": "vpn", "description": "🛡️ Панель управления и проверенные подписки"},
        {"command": "myvless", "description": "👑 Личный VLESS-ключ на твоём Render"},
        {"command": "check", "description": "🔄 Прогнать свежую пачку через Sing-box"},
        {"command": "ping", "description": "📊 Статус ядра и прокачанный трафик"},
    ]
    try:
        TG_SESSION.post(f"https://api.telegram.org/bot{TG_TOKEN}/setMyCommands", json={"commands": commands}, timeout=8)
    except Exception:
        pass


def send_vpn_dashboard():
    with VPN_LOCK:
        nodes = list(VPN_STATE["verified_nodes"])
        upd = VPN_STATE["last_updated"]
        sb_ok = VPN_STATE["singbox_ready"]
        tested = VPN_STATE["tested_total"]

    base_url = f"https://{RENDER_HOSTNAME or 'my-userbot-3j04.onrender.com'}"
    sub_url = f"{base_url}/sub?token={SUB_TOKEN}"
    sb_url = f"{base_url}/singbox?token={SUB_TOKEN}"

    top_preview = "\n".join(f"• <code>{html.escape(n['tag'])}</code>" for n in nodes[:6]) or "<i>Идёт загрузка ядра Sing-box и реальный тест трафика (~20 сек)...</i>"

    text = (
        f"🛡️ <b>Великий ВПН — Боевой режим (v5)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚙️ <b>Ядро проверки Sing-box:</b> {'🟢 Загружено' if sb_ok else '⏳ Скачивается...'}\n"
        f"🕒 <b>Проверка:</b> {html.escape(upd)} (прогнано: {tested})\n"
        f"💎 <b>Рабочих узлов (реальный HTTP 204):</b> {len(nodes)}\n\n"
        f"🏆 <b>Топ-6 живых серверов:</b>\n{top_preview}\n\n"
        f"🔗 <b>Подписка (Happ, v2rayNG, V2Box, Streisand):</b>\n<code>{html.escape(sub_url)}</code>\n\n"
        f"📦 <b>Профиль Sing-box (с прямым роутингом .ru):</b>\n<code>{html.escape(sb_url)}</code>"
    )
    buttons = [[
        {"text": "🔄 Запустить проверку", "callback_data": "run_check"},
        {"text": "👑 Мой личный ключ", "callback_data": "get_myvless"}
    ]]
    send_tg(text, buttons=buttons)


def run_telegram_listener():
    if not TG_TOKEN:
        return
    offset = 0
    set_tg_commands()
    send_tg("🛡️ <b>Великий ВПН v5 запущен!</b>\nКачаю бинарник <code>sing-box</code> для реального прогона трафика. Подожди 20 секунд и жми <code>/vpn</code>.", keyboard=True)

    while True:
        try:
            r = TG_SESSION.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25)
            if r.status_code == 200:
                for update in r.json().get("result", []):
                    offset = update["update_id"] + 1

                    cb = update.get("callback_query")
                    if cb:
                        if str(cb.get("message", {}).get("chat", {}).get("id", "")) != TG_ADMIN_ID:
                            continue
                        if cb["data"] == "run_check":
                            send_tg("🔄 <b>Запущен реальный тест узлов через Sing-box...</b>")
                            threading.Thread(target=execute_verified_harvest, args=(True,), daemon=True).start()
                        elif cb["data"] == "get_myvless":
                            send_tg(f"👑 <b>Твой личный VLESS на Render:</b>\n<code>{html.escape(get_self_vless_uri())}</code>")
                        continue

                    msg = update.get("message", {})
                    if str(msg.get("chat", {}).get("id", "")) != TG_ADMIN_ID:
                        continue
                    text = re.sub(r'^[🛡️👑🔄📊]\s*', '', msg.get("text", "").strip())

                    if text.startswith("/start"):
                        send_tg("Жми /vpn или /myvless", keyboard=True)
                    elif text.startswith("/vpn"):
                        send_vpn_dashboard()
                    elif text.startswith("/myvless"):
                        send_tg(f"👑 <b>Твой личный VLESS на Render:</b>\n<code>{html.escape(get_self_vless_uri())}</code>")
                    elif text.startswith("/check"):
                        send_tg("🔄 <b>Прогоняю свежую пачку через Sing-box...</b>")
                        threading.Thread(target=execute_verified_harvest, args=(True,), daemon=True).start()
                    elif text.startswith("/ping"):
                        with VPN_LOCK:
                            conns = VPN_STATE["relay_connections"]
                            mb = round(VPN_STATE["relay_bytes"] / (1024 * 1024), 2)
                            sb_ok = VPN_STATE["singbox_ready"]
                            cnt = len(VPN_STATE["verified_nodes"])
                        send_tg(
                            f"📊 <b>Диагностика:</b>\n"
                            f"Ядро Sing-box: {'Готово' if sb_ok else 'Нет'}\n"
                            f"Живых нод: {cnt}\n"
                            f"Личный VLESS сессий: {conns} ({mb} МБ)"
                        )
        except Exception:
            time.sleep(5)
        time.sleep(1)


if __name__ == "__main__":
    run_telegram_listener()
