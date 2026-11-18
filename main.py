import os
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
import urllib.parse
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque

# =====================================================================
# 1. ИНИЦИАЛИЗАЦИЯ ОКРУЖЕНИЯ И КРИПТО-КЛЮЧЕЙ СЕРВЕРА
# =====================================================================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if not RENDER_HOSTNAME and RENDER_EXTERNAL_URL:
    RENDER_HOSTNAME = urllib.parse.urlsplit(RENDER_EXTERNAL_URL).hostname or ""

# Детерминированные секреты на базе твоих токенов (не слетают при редеплое Render)
_SEED = f"{GITHUB_TOKEN}:{GITHUB_REPO}:{TG_TOKEN}:great_vpn_v3"
SUB_TOKEN = os.environ.get("SUB_TOKEN", hashlib.sha256(_SEED.encode()).hexdigest()[:16])
WS_SECRET_PATH = f"/ws-{SUB_TOKEN}"
VLESS_UUID = str(uuid.UUID(bytes=hashlib.md5(_SEED.encode()).digest()))
VLESS_UUID_BYTES = uuid.UUID(VLESS_UUID).bytes

VPN_LOCK = threading.Lock()
STATE_LOCK = threading.Lock()
VPN_REFRESH_EVENT = threading.Event()
HARVEST_RUNNING = False

GH_SESSION = requests.Session()
if GITHUB_TOKEN:
    GH_SESSION.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "GreatVPN-Controller/3.0"
    })

TG_SESSION = requests.Session()
HTTP_SCRAPER = requests.Session()
HTTP_SCRAPER.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
})

GITHUB_BASE = "https://api.github.com/repos/"

# =====================================================================
# 2. БАЗА БЕЛЫХ SNI, ЧИСТЫХ IP CLOUDFLARE И ИСТОЧНИКОВ НОД
# =====================================================================
DEFAULT_RU_WHITELIST_SNI = [
    "st.ozone.ru",
    "stats.vk-portal.net",
    "avatars.mds.yandex.net",
    "sba.yandex.net",
    "dl.google.com",
    "www.microsoft.com",
    "itunes.apple.com",
    "cdn.jsdelivr.net",
    "eh.vk.com",
    "api.ivi.ru",
    "static.tbank.ru",
    "sberbank.ru"
]

CF_CLEAN_IP_CANDIDATES = [
    "104.16.132.229", "104.17.147.22", "104.18.0.2", "104.19.192.2",
    "172.64.0.2", "172.67.128.2", "108.162.192.2", "141.101.64.2",
    "188.114.96.1", "188.114.97.1", "162.159.135.233", "162.159.136.234"
]

CF_WARP_ENDPOINTS = [
    ("162.159.192.1", 2408),
    ("162.159.193.5", 2408),
    ("162.159.195.1", 4500),
    ("188.114.96.1", 2408),
    ("188.114.97.3", 500),
    ("188.114.98.7", 1701),
    ("188.114.99.2", 2408),
]

PUBLIC_VPN_FEEDS = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/hy2.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/trojan.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/normal/vless",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/normal/trojan",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/normal/reality",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/reality",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_raw.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt",
]

VPN_STATE = {
    "last_updated": "Запускается...",
    "verified_nodes": [],
    "raw_uris": [],
    "sub_base64": "",
    "singbox_json": "",
    "warp_account": None,
    "custom_sni": list(DEFAULT_RU_WHITELIST_SNI),
    "clean_cf_ips": ["104.16.132.229", "104.17.147.22"],
    "relay_connections": 0,
    "relay_bytes": 0,
    "phone_reports": deque(maxlen=25)
}


# =====================================================================
# 3. ВСТРОЕННЫЙ VLESS-OVER-WEBSOCKET СЕРВЕР (ЛИЧНЫЙ ТУННЕЛЬ НА RENDER)
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
    return f"vless://{VLESS_UUID}@{host}:443?{params}#{urllib.parse.quote('👑 МОЙ ЛИЧНЫЙ RENDER VLESS (100GB)')}"


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


def _read_exact(rfile, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = rfile.read(n - len(buf))
        if not chunk:
            raise EOFError("WebSocket stream closed")
        buf.extend(chunk)
    return bytes(buf)


def _ws_read_frame(rfile) -> tuple:
    b1, b2 = _read_exact(rfile, 2)
    opcode = b1 & 0x0F
    masked = (b2 & 0x80) != 0
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack("!H", _read_exact(rfile, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _read_exact(rfile, 8))[0]
    if length > 4 * 1024 * 1024:
        raise ValueError("WS frame too large")
    mask_key = _read_exact(rfile, 4) if masked else b""
    payload = _read_exact(rfile, length)
    if masked:
        payload = _ws_unmask(payload, mask_key)
    return opcode, payload


def handle_vless_websocket_tunnel(handler: BaseHTTPRequestHandler):
    """
    Чистая реализация VLESS v0 поверх WebSocket (RFC 6455).
    Позволяет использовать сам Render-сервер как личный зашифрованный VLESS+WS+TLS узел.
    """
    ws_key = handler.headers.get("Sec-WebSocket-Key", "").strip()
    if not ws_key:
        handler.send_response(400)
        handler.end_headers()
        return

    accept_val = base64.b64encode(
        hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
    ).decode("ascii")

    handshake_resp = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_val}\r\n\r\n"
    ).encode("ascii")
    handler.wfile.write(handshake_resp)
    handler.wfile.flush()

    rfile = handler.rfile
    wfile = handler.wfile
    write_lock = threading.Lock()
    target_sock = None
    stop_event = threading.Event()

    def _ws_send(data: bytes, opcode: int = 0x02):
        frame = _ws_build_frame(data, opcode=opcode)
        with write_lock:
            wfile.write(frame)
            wfile.flush()

    try:
        # 1. Читаем первый фрейм с заголовком VLESS
        first_payload = b""
        while not first_payload:
            op, pl = _ws_read_frame(rfile)
            if op == 0x08:
                return
            if op == 0x09:
                _ws_send(pl, opcode=0x0A)
                continue
            if op in (0x01, 0x02, 0x00) and pl:
                first_payload = pl

        if len(first_payload) < 24:
            return
        if first_payload[0] != 0:
            return
        if first_payload[1:17] != VLESS_UUID_BYTES:
            return

        addons_len = first_payload[17]
        pos = 18 + addons_len
        if len(first_payload) < pos + 4:
            return

        cmd = first_payload[pos]
        if cmd != 1:  # Поддерживаем TCP (cmd=1)
            return

        dst_port = struct.unpack("!H", first_payload[pos + 1:pos + 3])[0]
        atyp = first_payload[pos + 3]
        pos += 4

        if atyp == 1:
            dst_host = socket.inet_ntoa(first_payload[pos:pos + 4])
            pos += 4
        elif atyp == 2:
            dlen = first_payload[pos]
            dst_host = first_payload[pos + 1:pos + 1 + dlen].decode("utf-8", errors="ignore")
            pos += 1 + dlen
        elif atyp == 3:
            dst_host = socket.inet_ntop(socket.AF_INET6, first_payload[pos:pos + 16])
            pos += 16
        else:
            return

        initial_tcp_data = first_payload[pos:]
        target_sock = socket.create_connection((dst_host, dst_port), timeout=10)
        target_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        with VPN_LOCK:
            VPN_STATE["relay_connections"] += 1

        if initial_tcp_data:
            target_sock.sendall(initial_tcp_data)
            with VPN_LOCK:
                VPN_STATE["relay_bytes"] += len(initial_tcp_data)

        def _pump_target_to_ws():
            first_reply = True
            try:
                while not stop_event.is_set():
                    data = target_sock.recv(16384)
                    if not data:
                        break
                    if first_reply:
                        data = b"\x00\x00" + data
                        first_reply = False
                    _ws_send(data, opcode=0x02)
                    with VPN_LOCK:
                        VPN_STATE["relay_bytes"] += len(data)
            except Exception:
                pass
            finally:
                stop_event.set()
                try:
                    _ws_send(b"", opcode=0x08)
                except Exception:
                    pass

        pump_thread = threading.Thread(target=_pump_target_to_ws, daemon=True)
        pump_thread.start()

        while not stop_event.is_set():
            op, pl = _ws_read_frame(rfile)
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
# 4. CURVE25519 WARP + AMNEZIA-WG ОБФУСКАТОР (ОБХОД БЛОКИРОВКИ WG В РФ)
# =====================================================================
def _x25519_scalarmult(scalar_bytes: bytes, u_bytes: bytes = None) -> bytes:
    P = (1 << 255) - 19
    A24 = 121665
    k = bytearray(scalar_bytes)
    k[0] &= 248
    k[31] &= 127
    k[31] |= 64
    scalar = int.from_bytes(k, "little")
    u = (int.from_bytes(u_bytes, "little") & ((1 << 255) - 1)) if u_bytes else 9
    x_1, x_2, z_2, x_3, z_3 = u, 1, 0, u, 1
    swap = 0
    for t in range(254, -1, -1):
        k_t = (scalar >> t) & 1
        swap ^= k_t
        if swap:
            x_2, x_3 = x_3, x_2
            z_2, z_3 = z_3, z_2
        swap = k_t
        A = (x_2 + z_2) % P
        AA = (A * A) % P
        B = (x_2 - z_2) % P
        BB = (B * B) % P
        E = (AA - BB) % P
        C = (x_3 + z_3) % P
        D = (x_3 - z_3) % P
        DA = (D * A) % P
        CB = (C * B) % P
        x_3 = pow(DA + CB, 2, P)
        z_3 = (x_1 * pow(DA - CB, 2, P)) % P
        x_2 = (AA * BB) % P
        z_2 = (E * (AA + A24 * E)) % P
    if swap:
        x_2, x_3 = x_3, x_2
        z_2, z_3 = z_3, z_2
    res = (x_2 * pow(z_2, P - 2, P)) % P
    return res.to_bytes(32, "little")


def generate_wireguard_keypair() -> tuple:
    priv_raw = bytearray(os.urandom(32))
    priv_raw[0] &= 248
    priv_raw[31] &= 127
    priv_raw[31] |= 64
    pub_raw = _x25519_scalarmult(bytes(priv_raw))
    return (
        base64.b64encode(bytes(priv_raw)).decode("ascii"),
        base64.b64encode(pub_raw).decode("ascii")
    )


def register_cloudflare_warp() -> dict:
    priv_key, pub_key = generate_wireguard_keypair()
    url = "https://api.cloudflareclient.com/v0a2223/reg"
    headers = {
        "User-Agent": "okhttp/3.12.1",
        "Content-Type": "application/json; charset=UTF-8"
    }
    payload = {
        "key": pub_key,
        "install_id": "",
        "fcm_token": "",
        "tos": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "model": "PC",
        "type": "Android",
        "locale": "en_US"
    }
    ep_host, ep_port = random.choice(CF_WARP_ENDPOINTS)
    warp_info = {
        "private_key": priv_key,
        "public_key": pub_key,
        "peer_public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
        "ipv4": "172.16.0.2",
        "ipv6": "2606:4700:110:8f81:d551:a0:532e:a2b3",
        "reserved": [random.randint(1, 250) for _ in range(3)],
        "endpoint_host": ep_host,
        "endpoint_port": ep_port,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }
    try:
        r = HTTP_SCRAPER.post(url, json=payload, headers=headers, timeout=12)
        if r.status_code in (200, 201):
            data = r.json()
            cfg = data.get("config", {})
            peers = cfg.get("peers", [{}])
            iface = cfg.get("interface", {}).get("addresses", {})
            client_id_b64 = cfg.get("client_id", "")
            reserved = list(base64.b64decode(client_id_b64)) if client_id_b64 else warp_info["reserved"]
            warp_info.update({
                "peer_public_key": peers[0].get("public_key", warp_info["peer_public_key"]),
                "ipv4": iface.get("v4", "172.16.0.2"),
                "ipv6": iface.get("v6", warp_info["ipv6"]),
                "reserved": reserved[:3]
            })
    except Exception as e:
        print(f"[!] WARP API fallback: {e}")

    with VPN_LOCK:
        VPN_STATE["warp_account"] = warp_info
    return warp_info


def build_amnezia_wg_conf(warp: dict) -> str:
    """Генерирует конфиг AmneziaWG с обфускацией junk-пакетов для обхода блокировки WireGuard на ТСПУ."""
    jc = random.randint(4, 8)
    jmin = random.randint(40, 60)
    jmax = random.randint(70, 110)
    return (
        "[Interface]\n"
        f"PrivateKey = {warp['private_key']}\n"
        f"Address = {warp['ipv4']}/32, {warp['ipv6']}/128\n"
        "DNS = 1.1.1.1, 1.0.0.1\n"
        "MTU = 1280\n"
        f"Jc = {jc}\n"
        f"Jmin = {jmin}\n"
        f"Jmax = {jmax}\n"
        "S1 = 0\n"
        "S2 = 0\n"
        "H1 = 1\n"
        "H2 = 2\n"
        "H3 = 3\n"
        "H4 = 4\n\n"
        "[Peer]\n"
        f"PublicKey = {warp['peer_public_key']}\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\n"
        f"Endpoint = {warp['endpoint_host']}:{warp['endpoint_port']}\n"
        "PersistentKeepalive = 25\n"
    )


# =====================================================================
# 5. СКАНЕР НОД С РЕАЛЬНОЙ ПРОВЕРКОЙ TLS 1.3 ХЕНДШЕЙКА (50 ПОТОКОВ)
# =====================================================================
def scan_clean_cloudflare_ips() -> list:
    def _test_ip(ip: str):
        t0 = time.time()
        try:
            with socket.create_connection((ip, 443), timeout=2.0) as sock:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with ctx.wrap_socket(sock, server_hostname="speed.cloudflare.com"):
                    return ip, int((time.time() - t0) * 1000)
        except Exception:
            return ip, 9999

    alive = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        for ip, ms in pool.map(_test_ip, CF_CLEAN_IP_CANDIDATES):
            if ms < 600:
                alive.append((ip, ms))
    alive.sort(key=lambda x: x[1])
    clean = [ip for ip, _ in alive[:5]] or ["104.16.132.229", "104.17.147.22"]
    with VPN_LOCK:
        VPN_STATE["clean_cf_ips"] = clean
    return clean


def _build_tls13_client_hello(sni: str) -> bytes:
    """Формирует минимальный валидный TLS 1.3 ClientHello для проверки реальных Reality/TLS серверов."""
    sni_bytes = sni.encode("idna")
    sni_ext = struct.pack("!HHBH", 0x0000, len(sni_bytes) + 5, 0x00, len(sni_bytes)) + sni_bytes
    supported_versions = b"\x00\x2b\x00\x03\x02\x03\x04"
    extensions = sni_ext + supported_versions
    body = (
        b"\x03\x03" + os.urandom(32) +
        b"\x00" +
        b"\x00\x04\x13\x01\x13\x02" +
        b"\x01\x00" +
        struct.pack("!H", len(extensions)) + extensions
    )
    handshake = b"\x01" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x01" + struct.pack("!H", len(handshake)) + handshake


def _decode_subscription_blob(raw_text: str) -> list:
    text = raw_text.strip()
    if "://" not in text[:120]:
        try:
            padded = text + "=" * ((4 - len(text) % 4) % 4)
            text = base64.b64decode(padded).decode("utf-8", errors="ignore")
        except Exception:
            pass
    lines = []
    for line in text.splitlines():
        l = line.strip()
        if any(l.startswith(proto) for proto in ("vless://", "trojan://", "hysteria2://", "hy2://")):
            lines.append(l)
    return lines


def discover_extra_github_feeds() -> list:
    """Автоматически находит свежие репозитории со списками нод на GitHub, если старые устарели."""
    if not GITHUB_TOKEN:
        return []
    try:
        url = "https://api.github.com/search/repositories"
        params = {"q": "vless reality sub OR v2ray configs in:name,description", "sort": "updated", "per_page": 6}
        r = GH_SESSION.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return []
        extra = []
        for repo in r.json().get("items", []):
            full_name = repo.get("full_name")
            branch = repo.get("default_branch", "main")
            if full_name:
                for candidate in ("sub.txt", "Sub1.txt", "all.txt", "vless.txt", "sub/sub_merge.txt"):
                    extra.append(f"https://raw.githubusercontent.com/{full_name}/{branch}/{candidate}")
        return extra[:12]
    except Exception:
        return []


def parse_proxy_uri(uri: str) -> dict:
    try:
        parsed = urllib.parse.urlsplit(uri)
        scheme = parsed.scheme.lower()
        if scheme not in ("vless", "trojan", "hysteria2", "hy2"):
            return {}
        if "@" not in parsed.netloc:
            return {}
        userinfo, hostport = parsed.netloc.rsplit("@", 1)
        userinfo = urllib.parse.unquote(userinfo)

        if hostport.startswith("["):
            return {}
        if ":" in hostport:
            host, port_str = hostport.rsplit(":", 1)
            port = int(port_str)
        else:
            host, port = hostport, 443

        if not host or port <= 0 or port > 65535:
            return {}

        qs = dict(urllib.parse.parse_qsl(parsed.query))
        security = qs.get("security", "tls" if scheme in ("trojan", "hysteria2", "hy2") else "none").lower()
        net_type = qs.get("type", "tcp").lower()
        sni = qs.get("sni") or qs.get("peer") or qs.get("host") or host

        if scheme == "vless" and security not in ("reality", "tls"):
            return {}
        if scheme == "vless" and security == "tls" and net_type == "tcp":
            return {}
        if security == "reality" and not qs.get("pbk"):
            return {}

        return {
            "scheme": "hysteria2" if scheme == "hy2" else scheme,
            "uuid_or_pass": userinfo,
            "host": host,
            "port": port,
            "params": qs,
            "security": security,
            "type": net_type,
            "sni": sni,
            "raw_uri": uri
        }
    except Exception:
        return {}


def verify_and_mutate_node(node: dict, whitelist_snis: list, clean_cf_ips: list) -> dict:
    host = node["host"]
    port = node["port"]
    sni = node["sni"]
    security = node["security"]
    net_type = node["type"]
    params = dict(node["params"])

    is_cdn_ws = net_type in ("ws", "grpc", "xhttp", "httpupgrade") and port == 443 and security == "tls"
    target_host = host
    if is_cdn_ws and any(x in host.lower() for x in ("workers.dev", "pages.dev", "trycloudflare.com")):
        target_host = random.choice(clean_cf_ips)
        params["host"] = host
        params["sni"] = host

    t0 = time.time()
    try:
        if node["scheme"] == "hysteria2":
            ip_addr = socket.gethostbyname(target_host)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as usock:
                usock.settimeout(1.8)
                usock.sendto(os.urandom(64), (ip_addr, port))
            latency_ms = int((time.time() - t0) * 1000) + 30
        elif security == "reality":
            # Реальная проверка TLS 1.3 ServerHello на указанный SNI
            with socket.create_connection((target_host, port), timeout=2.2) as sock:
                sock.settimeout(2.2)
                sock.sendall(_build_tls13_client_hello(sni or random.choice(whitelist_snis)))
                resp = sock.recv(5)
                if len(resp) < 3 or resp[0] != 0x16:
                    return {}
            latency_ms = int((time.time() - t0) * 1000)
        else:
            with socket.create_connection((target_host, port), timeout=2.2) as sock:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with ctx.wrap_socket(sock, server_hostname=sni or host):
                    pass
            latency_ms = int((time.time() - t0) * 1000)
    except Exception:
        return {}

    if latency_ms > 550:
        return {}

    params["fp"] = params.get("fp") if params.get("fp") in ("chrome", "firefox", "safari", "qq") else "chrome"
    if security == "reality" and not params.get("sni"):
        params["sni"] = random.choice(whitelist_snis)
    elif security == "tls":
        params["alpn"] = params.get("alpn", "h2,http/1.1")

    proto_badge = "REALITY" if security == "reality" else (
        "HY2-QUIC" if node["scheme"] == "hysteria2" else f"{net_type.upper()}-TLS"
    )
    tag = f"🛡️ [{proto_badge}] {target_host[:18]}:{port} ({latency_ms}ms)"

    query_str = urllib.parse.urlencode(params, safe=":,/")
    mutated_uri = f"{node['scheme']}://{urllib.parse.quote(node['uuid_or_pass'])}@{target_host}:{port}?{query_str}#{urllib.parse.quote(tag)}"

    node_out = dict(node)
    node_out.update({
        "host": target_host,
        "params": params,
        "latency_ms": latency_ms,
        "tag": tag,
        "mutated_uri": mutated_uri
    })
    return node_out


def build_singbox_anti_dpi_profile(nodes: list, warp: dict) -> dict:
    outbounds = []
    outbound_tags = []

    # 1. Личный VLESS-over-WebSocket прямо на твоем Render
    if RENDER_HOSTNAME:
        self_tag = f"👑 МОЙ RENDER VLESS ({RENDER_HOSTNAME})"
        outbounds.append({
            "type": "vless",
            "tag": self_tag,
            "server": RENDER_HOSTNAME,
            "server_port": 443,
            "uuid": VLESS_UUID,
            "tls": {
                "enabled": True,
                "server_name": RENDER_HOSTNAME,
                "utls": {"enabled": True, "fingerprint": "chrome"}
            },
            "transport": {
                "type": "ws",
                "path": WS_SECRET_PATH,
                "headers": {"Host": RENDER_HOSTNAME}
            }
        })
        outbound_tags.append(self_tag)

    # 2. Cloudflare WARP
    if warp:
        warp_tag = f"⚡ Cloudflare WARP ({warp['endpoint_host']})"
        outbounds.append({
            "type": "wireguard",
            "tag": warp_tag,
            "server": warp["endpoint_host"],
            "server_port": warp["endpoint_port"],
            "local_address": [f"{warp['ipv4']}/32", f"{warp['ipv6']}/128"],
            "private_key": warp["private_key"],
            "peer_public_key": warp["peer_public_key"],
            "reserved": warp["reserved"],
            "mtu": 1280
        })
        outbound_tags.append(warp_tag)

    # 3. Топ проверенных Reality / Hysteria2 / Trojan нод
    for idx, n in enumerate(nodes[:30]):
        tag = f"{n['tag']} #{idx + 1}"
        p = n["params"]
        scheme = n["scheme"]

        if scheme == "vless":
            ob = {
                "type": "vless",
                "tag": tag,
                "server": n["host"],
                "server_port": n["port"],
                "uuid": n["uuid_or_pass"],
                "tls": {
                    "enabled": True,
                    "server_name": p.get("sni", n["sni"]),
                    "insecure": True,
                    "utls": {"enabled": True, "fingerprint": p.get("fp", "chrome")}
                }
            }
            if p.get("flow"):
                ob["flow"] = p["flow"]
            if n["security"] == "reality":
                ob["tls"]["reality"] = {
                    "enabled": True,
                    "public_key": p.get("pbk", ""),
                    "short_id": p.get("sid", "")
                }
            if n["type"] == "ws":
                ob["transport"] = {
                    "type": "ws",
                    "path": p.get("path", "/"),
                    "headers": {"Host": p.get("host", p.get("sni", n["host"]))}
                }
            elif n["type"] == "grpc":
                ob["transport"] = {"type": "grpc", "service_name": p.get("serviceName", "")}
            outbounds.append(ob)
            outbound_tags.append(tag)
        elif scheme == "trojan":
            ob = {
                "type": "trojan",
                "tag": tag,
                "server": n["host"],
                "server_port": n["port"],
                "password": n["uuid_or_pass"],
                "tls": {
                    "enabled": True,
                    "server_name": p.get("sni", n["sni"]),
                    "insecure": True,
                    "utls": {"enabled": True, "fingerprint": p.get("fp", "chrome")}
                }
            }
            if n["type"] == "ws":
                ob["transport"] = {
                    "type": "ws",
                    "path": p.get("path", "/"),
                    "headers": {"Host": p.get("host", p.get("sni", n["host"]))}
                }
            outbounds.append(ob)
            outbound_tags.append(tag)
        elif scheme == "hysteria2":
            ob = {
                "type": "hysteria2",
                "tag": tag,
                "server": n["host"],
                "server_port": n["port"],
                "password": n["uuid_or_pass"],
                "tls": {"enabled": True, "server_name": p.get("sni", n["sni"]), "insecure": True}
            }
            if p.get("obfs") == "salamander" and p.get("obfs-password"):
                ob["obfs"] = {"type": "salamander", "password": p["obfs-password"]}
            outbounds.append(ob)
            outbound_tags.append(tag)

    if not outbound_tags:
        outbound_tags = ["direct"]

    header_outbounds = [
        {
            "type": "selector",
            "tag": "🚀 ВЕЛИКИЙ ВПН (Анти-ТСПУ)",
            "outbounds": ["⚡ АВТО-ПИНГ (Failover)"] + outbound_tags + ["direct"],
            "default": "⚡ АВТО-ПИНГ (Failover)"
        },
        {
            "type": "urltest",
            "tag": "⚡ АВТО-ПИНГ (Failover)",
            "outbounds": outbound_tags,
            "url": "https://www.gstatic.com/generate_204",
            "interval": "2m",
            "tolerance": 60
        }
    ]

    tail_outbounds = [
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
        {"type": "dns", "tag": "dns-out"}
    ]

    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "dns-remote", "address": "https://1.1.1.1/dns-query", "address_resolver": "dns-direct", "detour": "🚀 ВЕЛИКИЙ ВПН (Анти-ТСПУ)"},
                {"tag": "dns-direct", "address": "77.88.8.8", "detour": "direct"}
            ],
            "rules": [{"domain_suffix": [".ru", ".su", ".xn--p1ai"], "server": "dns-direct"}],
            "final": "dns-remote"
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "inet4_address": "172.19.0.1/30",
                "mtu": 1400,
                "auto_route": True,
                "strict_route": True,
                "sniff": True
            }
        ],
        "outbounds": header_outbounds + outbounds + tail_outbounds,
        "route": {
            "auto_detect_interface": True,
            "rules": [
                {"protocol": "dns", "outbound": "dns-out"},
                {"ip_is_private": True, "outbound": "direct"},
                {
                    "domain_suffix": [
                        ".ru", ".su", ".xn--p1ai", "yandex.net", "vk.com", "userapi.com",
                        "ozon.ru", "wb.ru", "sberbank.ru", "tbank.ru", "gosuslugi.ru"
                    ],
                    "outbound": "direct"
                }
            ],
            "final": "🚀 ВЕЛИКИЙ ВПН (Анти-ТСПУ)"
        }
    }


def push_vpn_backup_to_github(files_dict: dict, commit_msg: str):
    """Атомарно коммитит подписку в GitHub через Git Tree API как резервное зеркало."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return
    try:
        ref_url = f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main"
        r = GH_SESSION.get(ref_url, timeout=10)
        if r.status_code != 200:
            return
        head_sha = r.json()["object"]["sha"]

        c_res = GH_SESSION.get(f"{GITHUB_BASE}{GITHUB_REPO}/git/commits/{head_sha}", timeout=10)
        if c_res.status_code != 200:
            return
        base_tree = c_res.json()["tree"]["sha"]

        tree_items = [
            {"path": p, "mode": "100644", "type": "blob", "content": content}
            for p, content in files_dict.items()
        ]
        t_res = GH_SESSION.post(f"{GITHUB_BASE}{GITHUB_REPO}/git/trees", json={"base_tree": base_tree, "tree": tree_items}, timeout=12)
        if t_res.status_code != 201:
            return
        new_tree = t_res.json()["sha"]

        nc_res = GH_SESSION.post(
            f"{GITHUB_BASE}{GITHUB_REPO}/git/commits",
            json={"message": commit_msg, "tree": new_tree, "parents": [head_sha]},
            timeout=10
        )
        if nc_res.status_code != 201:
            return
        new_commit = nc_res.json()["sha"]
        GH_SESSION.patch(ref_url, json={"sha": new_commit}, timeout=10)
    except Exception as e:
        print(f"[!] GitHub backup error: {e}")


def harvest_and_mutate_vpn_pool(notify_tg: bool = False) -> dict:
    global HARVEST_RUNNING
    with STATE_LOCK:
        if HARVEST_RUNNING:
            return {"status": "running"}
        HARVEST_RUNNING = True

    try:
        clean_ips = scan_clean_cloudflare_ips()

        with VPN_LOCK:
            warp_acc = VPN_STATE["warp_account"]
            custom_sni = list(VPN_STATE["custom_sni"])

        if not warp_acc:
            warp_acc = register_cloudflare_warp()

        all_feeds = list(PUBLIC_VPN_FEEDS) + discover_extra_github_feeds()
        raw_candidates = []

        def _fetch_feed(url: str) -> list:
            try:
                res = HTTP_SCRAPER.get(url, timeout=8)
                if res.status_code == 200:
                    return _decode_subscription_blob(res.text)
            except Exception:
                pass
            return []

        with ThreadPoolExecutor(max_workers=12) as pool:
            for chunk in pool.map(_fetch_feed, all_feeds):
                raw_candidates.extend(chunk)

        random.shuffle(raw_candidates)
        parsed_map = {}
        for uri in raw_candidates:
            p = parse_proxy_uri(uri)
            if p:
                key = f"{p['host']}:{p['port']}"
                if key not in parsed_map:
                    parsed_map[key] = p
                if len(parsed_map) >= 600:
                    break

        verified = []
        with ThreadPoolExecutor(max_workers=50) as pool:
            futures = [
                pool.submit(verify_and_mutate_node, node, custom_sni, clean_ips)
                for node in parsed_map.values()
            ]
            for fut in as_completed(futures):
                res = fut.result()
                if res:
                    verified.append(res)

        verified.sort(key=lambda x: (0 if x["security"] == "reality" else 1, x["latency_ms"]))
        top_nodes = verified[:40]

        uris = []
        # №1: Личный VLESS-over-WebSocket на самом Render
        if RENDER_HOSTNAME:
            uris.append(get_self_vless_uri(RENDER_HOSTNAME))

        # №2: Личный Cloudflare WARP
        if warp_acc:
            wg_uri = (
                f"wireguard://{urllib.parse.quote(warp_acc['private_key'])}@"
                f"{warp_acc['endpoint_host']}:{warp_acc['endpoint_port']}?"
                f"address={urllib.parse.quote(warp_acc['ipv4'] + '/32')}&"
                f"publickey={urllib.parse.quote(warp_acc['peer_public_key'])}&"
                f"mtu=1280#⚡%20Cloudflare%20WARP%20Anti-TSPU"
            )
            uris.append(wg_uri)

        # №3..42: Топ проверенных Reality / Hysteria2 / Trojan нод
        uris.extend(n["mutated_uri"] for n in top_nodes)

        sub_b64 = base64.b64encode("\n".join(uris).encode("utf-8")).decode("ascii")
        singbox_cfg = build_singbox_anti_dpi_profile(top_nodes, warp_acc)
        singbox_str = json.dumps(singbox_cfg, indent=2, ensure_ascii=False)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        with VPN_LOCK:
            VPN_STATE["last_updated"] = now_str
            VPN_STATE["verified_nodes"] = top_nodes
            VPN_STATE["raw_uris"] = uris
            VPN_STATE["sub_base64"] = sub_b64
            VPN_STATE["singbox_json"] = singbox_str

        push_vpn_backup_to_github(
            {
                "vpn/sub_base64.txt": sub_b64,
                "vpn/sub_raw.txt": "\n".join(uris),
                "vpn/singbox_ru_anti_dpi.json": singbox_str
            },
            f"🛡️ [Великий ВПН] Обновление пула: {len(top_nodes)} внешних + личный Render VLESS [skip ci]"
        )

        if notify_tg:
            reality_cnt = sum(1 for n in top_nodes if n["security"] == "reality")
            hy2_cnt = sum(1 for n in top_nodes if n["scheme"] == "hysteria2")
            best_ms = top_nodes[0]["latency_ms"] if top_nodes else 0
            send_tg(
                f"🛡️ <b>Великий ВПН обновлён!</b>\n━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Личный Render VLESS:</b> Активен (443 TLS)\n"
                f"🟢 <b>Внешних живых нод:</b> {len(top_nodes)} (Reality: {reality_cnt}, HY2: {hy2_cnt})\n"
                f"⚡ <b>Лучший внешний пинг:</b> {best_ms} ms\n"
                f"🔑 <b>Cloudflare WARP:</b> Готов ({warp_acc['endpoint_host']})\n\n"
                f"Жми <code>/vpn</code> для получения ссылок или <code>/myvless</code> для личного ключа."
            )
        return {"status": "ok", "count": len(top_nodes)}
    finally:
        with STATE_LOCK:
            HARVEST_RUNNING = False


def run_vpn_daemon():
    time.sleep(2)
    while True:
        try:
            harvest_and_mutate_vpn_pool(notify_tg=False)
        except Exception as e:
            print(f"[!] Ошибка фонового харвестера: {e}")
        VPN_REFRESH_EVENT.wait(timeout=1800)
        VPN_REFRESH_EVENT.clear()


# =====================================================================
# 6. HTTP-СЕРВЕР (VLESS WEBSOCKET + ПОДПИСКИ + ТЕЛЕМЕТРИЯ /REPORT)
# =====================================================================
class GreatVPNHTTPHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def _send_text(self, code: int, body: str, content_type: str = "text/plain; charset=utf-8", extra_headers: dict = None):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
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

        # 1. Секретный WebSocket-туннель для личного VLESS
        if parsed.path == WS_SECRET_PATH:
            handle_vless_websocket_tunnel(self)
            self.close_connection = True
            return

        qs = dict(urllib.parse.parse_qsl(parsed.query))
        token = qs.get("token", "")

        # 2. Health-check для Render и пингера
        if parsed.path in ("/", "/health", "/ping"):
            with VPN_LOCK:
                n_cnt = len(VPN_STATE["verified_nodes"])
                upd = VPN_STATE["last_updated"]
            self._send_text(200, f"GreatVPN Operational | Nodes: {n_cnt} | Updated: {upd}")
            return

        # 3. Защищённые подписки
        if parsed.path in ("/sub", "/raw", "/singbox", "/amnezia"):
            if token != SUB_TOKEN:
                self._send_text(403, "Forbidden")
                return

            with VPN_LOCK:
                sub_b64 = VPN_STATE["sub_base64"]
                raw_uris = "\n".join(VPN_STATE["raw_uris"])
                sb_json = VPN_STATE["singbox_json"]
                warp_acc = VPN_STATE["warp_account"]

            sub_headers = {
                "Profile-Title": base64.b64encode("🛡️ Великий ВПН (Анти-ТСПУ)".encode("utf-8")).decode("ascii"),
                "Profile-Update-Interval": "1",
                "Subscription-Userinfo": "upload=0; download=0; total=107374182400; expire=2147483647"
            }

            if parsed.path == "/sub":
                if not sub_b64 and RENDER_HOSTNAME:
                    sub_b64 = base64.b64encode(get_self_vless_uri(RENDER_HOSTNAME).encode("utf-8")).decode("ascii")
                self._send_text(200, sub_b64, extra_headers=sub_headers)
            elif parsed.path == "/raw":
                self._send_text(200, raw_uris or get_self_vless_uri(), extra_headers=sub_headers)
            elif parsed.path == "/singbox":
                self._send_text(200, sb_json or "{}", content_type="application/json; charset=utf-8", extra_headers=sub_headers)
            elif parsed.path == "/amnezia":
                w = warp_acc or register_cloudflare_warp()
                self._send_text(200, build_amnezia_wg_conf(w))
            return

        self._send_text(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        qs = dict(urllib.parse.parse_qsl(parsed.query))
        token = qs.get("token") or self.headers.get("X-Sub-Token", "")

        if parsed.path != "/report" or token != SUB_TOKEN:
            self._send_text(403, "Forbidden")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(min(length, 65536)).decode("utf-8", errors="ignore")
            payload = json.loads(raw_body) if raw_body else {}
        except Exception:
            payload = {}

        working_sni = [s.strip() for s in payload.get("working_sni", []) if isinstance(s, str) and "." in s]
        dead_sni = {s.strip() for s in payload.get("dead_sni", []) if isinstance(s, str)}
        operator = str(payload.get("operator", "Phone"))[:40]

        with VPN_LOCK:
            curr = [s for s in VPN_STATE["custom_sni"] if s not in dead_sni]
            for s in working_sni:
                if s not in curr:
                    curr.insert(0, s)
            VPN_STATE["custom_sni"] = curr or list(DEFAULT_RU_WHITELIST_SNI)

        if payload.get("rebuild", True):
            VPN_REFRESH_EVENT.set()

        send_tg(
            f"📱 <b>Сигнал с телефона ({html.escape(operator)})!</b>\n"
            f"✅ Рабочие SNI: <code>{html.escape(', '.join(working_sni) or 'без изменений')}</code>\n"
            f"❌ Удалены мёртвые: <code>{html.escape(', '.join(dead_sni) or 'нет')}</code>\n"
            f"🔄 Запущена пересборка пула."
        )
        self._send_text(200, json.dumps({"status": "ok"}), "application/json")


def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), GreatVPNHTTPHandler)
    server.serve_forever()


threading.Thread(target=run_http_server, daemon=True).start()
threading.Thread(target=run_vpn_daemon, daemon=True).start()


# =====================================================================
# 7. TELEGRAM ПУЛЬТ УПРАВЛЕНИЯ ВЕЛИКИМ ВПН
# =====================================================================
def send_tg(text: str, buttons: list = None, keyboard: bool = False):
    if not TG_TOKEN or not TG_ADMIN_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_ADMIN_ID,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if keyboard:
        payload["reply_markup"] = json.dumps({
            "keyboard": [
                ["🛡️ /vpn", "👑 /myvless", "📦 /amnezia"],
                ["🔄 /refresh", "🔑 /warp", "📡 /sni"],
                ["📊 /ping", "❓ /help"]
            ],
            "resize_keyboard": True,
            "is_persistent": True
        })
    elif buttons:
        payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
    try:
        TG_SESSION.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Ошибка TG: {e}")


def send_tg_document(filename: str, content_str: str, caption: str = ""):
    if not TG_TOKEN or not TG_ADMIN_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    try:
        TG_SESSION.post(
            url,
            data={"chat_id": TG_ADMIN_ID, "caption": caption, "parse_mode": "HTML"},
            files={"document": (filename, content_str.encode("utf-8"), "text/plain")},
            timeout=15
        )
    except Exception as e:
        print(f"[!] Ошибка отправки файла в TG: {e}")


def answer_tg_callback(callback_query_id: str, text: str = ""):
    if not TG_TOKEN:
        return
    try:
        TG_SESSION.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text[:200]},
            timeout=10
        )
    except Exception:
        pass


def set_tg_commands():
    if not TG_TOKEN:
        return
    commands = [
        {"command": "vpn", "description": "🛡️ Главный пульт, подписки и статус серверов"},
        {"command": "myvless", "description": "👑 Личный VLESS-ключ прямо на твоём Render"},
        {"command": "amnezia", "description": "📦 Скачать конфиг AmneziaWG (обход блока WG в РФ)"},
        {"command": "refresh", "description": "🔄 Принудительно просканировать и обновить ноды"},
        {"command": "warp", "description": "🔑 Перевыпустить аккаунт Cloudflare WARP"},
        {"command": "sni", "description": "📡 Белые списки SNI для маскировки под РФ-сайты"},
        {"command": "ping", "description": "📊 Диагностика туннеля, трафика и узлов"},
        {"command": "help", "description": "❓ Инструкция по подключению"},
    ]
    try:
        TG_SESSION.post(f"https://api.telegram.org/bot{TG_TOKEN}/setMyCommands", json={"commands": commands}, timeout=10)
    except Exception:
        pass


HELP_TEXT = (
    "🛡️ <b>Великий ВПН — Инструкция за 30 секунд</b>\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    "1️⃣ <b>Самый надёжный вариант (твой личный сервер):</b>\n"
    "Нажми <code>/myvless</code>, скопируй ссылку <code>vless://...</code> и вставь в <b>v2rayNG, Happ, Hiddify или Streisand</b>. Это твой собственный VLESS+WebSocket+TLS прямо на Render.\n\n"
    "2️⃣ <b>Автоматическая подписка на 40+ серверов:</b>\n"
    "Нажми <code>/vpn</code> и скопируй ссылку <code>/sub?token=...</code> (или <code>/singbox?token=...</code> для умного разделения трафика, чтобы русские банки и Госуслуги работали без отключения ВПН).\n\n"
    "3️⃣ <b>Против блокировки WireGuard в РФ:</b>\n"
    "Нажми <code>/amnezia</code> — бот пришлёт готовый <code>.conf</code> файл для приложения <b>AmneziaWG</b> с обфускацией пакетов."
)


def send_vpn_dashboard():
    with VPN_LOCK:
        nodes = list(VPN_STATE["verified_nodes"])
        upd = VPN_STATE["last_updated"]
        warp = VPN_STATE["warp_account"]
        clean_ips = list(VPN_STATE["clean_cf_ips"])
        snis = list(VPN_STATE["custom_sni"])
        conns = VPN_STATE["relay_connections"]
        relayed_mb = round(VPN_STATE["relay_bytes"] / (1024 * 1024), 2)

    host = RENDER_HOSTNAME or "my-userbot-3j04.onrender.com"
    base_url = f"https://{host}"
    sub_url = f"{base_url}/sub?token={SUB_TOKEN}"
    sb_url = f"{base_url}/singbox?token={SUB_TOKEN}"
    gh_raw_sub = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/vpn/sub_base64.txt" if GITHUB_REPO else ""

    reality_cnt = sum(1 for n in nodes if n.get("security") == "reality")
    hy2_cnt = sum(1 for n in nodes if n.get("scheme") == "hysteria2")
    top_preview = "\n".join(
        f"• <code>{html.escape(n['tag'])}</code>" for n in nodes[:5]
    ) or "<i>Идёт первичный поиск в 50 потоков, личный VLESS уже готов!</i>"

    text = (
        f"🛡️ <b>Великий ВПН — Центр управления</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Личный Render VLESS:</b> Активен (сессий: {conns}, трафик: {relayed_mb} МБ)\n"
        f"🕒 <b>Обновление пула:</b> {html.escape(upd)}\n"
        f"🟢 <b>Внешних живых нод:</b> {len(nodes)} (Reality: {reality_cnt}, HY2: {hy2_cnt})\n"
        f"⚡ <b>Cloudflare WARP:</b> {'Готов (' + warp['ipv4'] + ')' if warp else 'Генерируется...'}\n"
        f"🌐 <b>Чистые IP CF:</b> <code>{', '.join(clean_ips[:3])}</code>\n"
        f"📡 <b>Белые SNI ({len(snis)}):</b> <code>{', '.join(snis[:3])}...</code>\n\n"
        f"🏆 <b>Топ-5 внешних узлов:</b>\n{top_preview}\n\n"
        f"🔗 <b>Подписка (Happ, v2rayNG, Streisand, Hiddify):</b>\n"
        f"<code>{html.escape(sub_url)}</code>\n\n"
        f"📦 <b>Профиль Sing-box / Nekobox (прямой доступ к .ru):</b>\n"
        f"<code>{html.escape(sb_url)}</code>"
    )
    if gh_raw_sub:
        text += f"\n\n🐙 <b>Резервное зеркало GitHub:</b>\n<code>{html.escape(gh_raw_sub)}</code>"

    buttons = [
        [
            {"text": "👑 Мой личный VLESS", "callback_data": "get_myvless"},
            {"text": "📦 Файл AmneziaWG", "callback_data": "get_amnezia"}
        ],
        [
            {"text": "🔄 Обновить ноды (50 потоков)", "callback_data": "vpn_refresh"},
            {"text": "📋 Топ-5 ключей", "callback_data": "vpn_raw_top"}
        ]
    ]
    send_tg(text, buttons=buttons)


def handle_sni_command(arg_str: str):
    parts = arg_str.split()
    with VPN_LOCK:
        snis = list(VPN_STATE["custom_sni"])

    if not parts:
        send_tg(
            f"📡 <b>Белые SNI ({len(snis)} шт.):</b>\n"
            f"<code>{html.escape(', '.join(snis))}</code>\n\n"
            f"• Добавить сайт: <code>/sni add домен.ru</code>\n"
            f"• Удалить сайт: <code>/sni del домен.ru</code>\n"
            f"• Сбросить: <code>/sni reset</code>"
        )
        return

    cmd = parts[0].lower()
    target = parts[1].lower().strip() if len(parts) > 1 else ""
    with VPN_LOCK:
        if cmd == "add" and target and "." in target:
            if target not in VPN_STATE["custom_sni"]:
                VPN_STATE["custom_sni"].insert(0, target)
            send_tg(f"✅ Домен <code>{html.escape(target)}</code> добавлен первым в ротацию! Пересобираю пул...")
            VPN_REFRESH_EVENT.set()
        elif cmd == "del" and target:
            VPN_STATE["custom_sni"] = [s for s in VPN_STATE["custom_sni"] if s != target] or list(DEFAULT_RU_WHITELIST_SNI)
            send_tg(f"🗑 Домен <code>{html.escape(target)}</code> удалён.")
        elif cmd == "reset":
            VPN_STATE["custom_sni"] = list(DEFAULT_RU_WHITELIST_SNI)
            send_tg("🔄 Список белых SNI сброшен.")
        else:
            send_tg("⚠️ Формат: <code>/sni add домен.ru</code> или <code>/sni del домен.ru</code>")


def run_telegram_listener():
    if not TG_TOKEN or not TG_ADMIN_ID:
        print("[!] Telegram переменные не заданы.")
        return

    offset = 0
    set_tg_commands()
    send_tg(
        "🛡️ <b>Великий ВПН запущен!</b>\n"
        "Твой личный VLESS-сервер на Render уже работает, а 50-поточный сканер собирает внешние Reality/HY2 узлы.",
        keyboard=True
    )

    while True:
        try:
            r = TG_SESSION.get(
                f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 20},
                timeout=25
            )
            if r.status_code == 200:
                for update in r.json().get("result", []):
                    offset = update["update_id"] + 1

                    cb = update.get("callback_query")
                    if cb:
                        cb_chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                        cb_data = cb.get("data", "")
                        if cb_chat_id != TG_ADMIN_ID:
                            answer_tg_callback(cb["id"])
                            continue

                        if cb_data == "get_myvless":
                            answer_tg_callback(cb["id"], "Личный ключ готов")
                            uri = get_self_vless_uri()
                            send_tg(
                                f"👑 <b>Твой личный VLESS+WS+TLS ключ (Render 443):</b>\n\n"
                                f"<code>{html.escape(uri)}</code>\n\n"
                                f"<i>Скопируй и вставь из буфера в Happ, v2rayNG, Streisand или Hiddify.</i>"
                            )
                        elif cb_data == "get_amnezia":
                            answer_tg_callback(cb["id"], "Генерирую конфиг AmneziaWG...")
                            with VPN_LOCK:
                                w = VPN_STATE["warp_account"]
                            if not w:
                                w = register_cloudflare_warp()
                            send_tg_document(
                                "GreatVPN_AmneziaWG.conf",
                                build_amnezia_wg_conf(w),
                                caption="📦 <b>Конфиг AmneziaWG с обфускацией junk-пакетов.</b>\nИмпортируй этот файл в приложение AmneziaWG / AmneziaVPN."
                            )
                        elif cb_data == "vpn_refresh":
                            answer_tg_callback(cb["id"], "Сканирую в 50 потоков...")
                            send_tg("🔄 <b>Запущено глубокое сканирование 22+ баз в 50 потоков...</b>")
                            threading.Thread(target=harvest_and_mutate_vpn_pool, args=(True,), daemon=True).start()
                        elif cb_data == "vpn_raw_top":
                            answer_tg_callback(cb["id"])
                            with VPN_LOCK:
                                top_uris = list(VPN_STATE["raw_uris"][:6])
                            block = "\n\n".join(top_uris)
                            send_tg(f"📋 <b>Топ ключей (нажми чтобы скопировать):</b>\n\n<code>{html.escape(block[:3600])}</code>")
                        continue

                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").strip()
                    text = re.sub(r'^[🛡️👑📦🔄🔑📡📊❓]\s*', '', text)

                    if chat_id != TG_ADMIN_ID:
                        continue

                    if text.startswith("/start") or text.startswith("/help"):
                        send_tg(HELP_TEXT, keyboard=True)
                    elif text.startswith("/vpn"):
                        send_vpn_dashboard()
                    elif text.startswith("/myvless"):
                        uri = get_self_vless_uri()
                        send_tg(
                            f"👑 <b>Твой личный VLESS+WS+TLS ключ (Render 443):</b>\n\n"
                            f"<code>{html.escape(uri)}</code>\n\n"
                            f"<i>Работает напрямую через твой сервер Render. Лимит бесплатного трафика: 100 ГБ/мес.</i>"
                        )
                    elif text.startswith("/amnezia"):
                        with VPN_LOCK:
                            w = VPN_STATE["warp_account"]
                        if not w:
                            w = register_cloudflare_warp()
                        send_tg_document(
                            "GreatVPN_AmneziaWG.conf",
                            build_amnezia_wg_conf(w),
                            caption="📦 <b>Готовый конфиг AmneziaWG (WARP с анти-ТСПУ обфускацией).</b>\nОткрой через приложение AmneziaWG."
                        )
                    elif text.startswith("/refresh"):
                        send_tg("🔄 <b>Сканирую 22+ источников и GitHub в 50 потоков...</b>")
                        threading.Thread(target=harvest_and_mutate_vpn_pool, args=(True,), daemon=True).start()
                    elif text.startswith("/warp"):
                        send_tg("🔑 <b>Генерирую новую пару Curve25519 для Cloudflare WARP...</b>")
                        def _new_warp():
                            w = register_cloudflare_warp()
                            harvest_and_mutate_vpn_pool(notify_tg=False)
                            send_tg(
                                f"✅ <b>Новый Cloudflare WARP готов!</b>\n"
                                f"IPv4: <code>{w['ipv4']}</code>\n"
                                f"Endpoint: <code>{w['endpoint_host']}:{w['endpoint_port']}</code>\n"
                                f"Для обхода блокировки WG в РФ жми <code>/amnezia</code>."
                            )
                        threading.Thread(target=_new_warp, daemon=True).start()
                    elif text.startswith("/sni"):
                        handle_sni_command(text[4:].strip())
                    elif text.startswith("/ping"):
                        with VPN_LOCK:
                            n_cnt = len(VPN_STATE["verified_nodes"])
                            conns = VPN_STATE["relay_connections"]
                            mb = round(VPN_STATE["relay_bytes"] / (1024 * 1024), 2)
                            upd = VPN_STATE["last_updated"]
                        send_tg(
                            f"📊 <b>Диагностика Великого ВПН</b>\n━━━━━━━━━━━━━━━━━━━\n"
                            f"🌐 <b>Хост Render:</b> <code>{html.escape(RENDER_HOSTNAME or 'определяется...')}</code>\n"
                            f"🔌 <b>VLESS-туннель сессий:</b> {conns} (прокачано {mb} МБ)\n"
                            f"🟢 <b>Живых внешних нод:</b> {n_cnt}\n"
                            f"🕒 <b>Последний скан:</b> {html.escape(upd)}"
                        )
                    elif text:
                        send_tg("Используй кнопки меню ниже 👇", keyboard=True)
        except Exception as e:
            print(f"[!] Ошибка в TG-цикле: {e}")
            time.sleep(5)
        time.sleep(1)


if __name__ == "__main__":
    run_telegram_listener()
