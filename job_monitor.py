import os
import re
import json
import time
import logging
from pathlib import Path
import urllib.request
import urllib.parse
import html
import feedparser
import schedule

# ----------------------------------------------------------------------
# CONFIGURACIÓN TELEGRAM Y PORTFOLIO
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).parent

TELEGRAM_BOT_TOKEN = "8958926765:AAHka_dr0e4kewtgyY-D0pgilYLx85wXO4w"
TELEGRAM_CHAT_ID = "708457190"
PORTFOLIO_URL = "https://pepm83-arch.github.io/Portfolio"

# Cabecera realista de navegador para evitar bloqueos 403 / anti-scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 JobMonitor/1.0"
}

# 1. FUENTES RSS CONFIGURADAS (Mercado hispanohablante e internacional)
FEEDS = [
    {
        "name": "Notodoanimacion (España/Latam 3D)",
        "url": "https://www.notodoanimacion.es/feed/"
    },
    {
        "name": "Reddit r/gameDevClassifieds",
        "url": "https://www.reddit.com/r/gameDevClassifieds/new/.rss"
    },
    {
        "name": "Reddit r/INAT (I Need A Team)",
        "url": "https://www.reddit.com/r/INAT/new/.rss"
    },
    {
        "name": "Reddit r/3Dmodeling",
        "url": "https://www.reddit.com/r/3Dmodeling/new/.rss"
    },
    {
        "name": "Remotive Remote Jobs",
        "url": "https://remotive.com/remote-jobs/feed"
    },
    {
        "name": "WeWorkRemotely Design & 3D",
        "url": "https://weworkremotely.com/categories/remote-design-jobs.rss"
    }
]

# 2. FILTRADO QUIRÚRGICO DE OFERTAS

# Términos requeridos de alta relevancia en Arte / Modelado 3D
REQUIRED_3D_KEYWORDS = [
    r"\b3d\b",
    r"\bmodeler\b",
    r"\bmodelador\b",
    r"\bprops?\b",
    r"\bcharacter\b",
    r"\benvironment\b",
    r"\basset\b",
    r"\bminiature\b",
    r"\bminiaturas?\b",
    r"\bfigure\b",
    r"\bfigura\b",
    r"\bblender\b",
    r"\bzbrush\b",
    r"\bhardsurface\b",
    r"\bhard-surface\b",
    r"\btextur(?:ing|e)\b",
    r"\bsculpt(?:or|ing)?\b",
    r"\bescult(?:or|ura)?\b"
]

# Términos corporativos / ajenos al arte para descarte inmediato si aparecen en el título
EXCLUDED_TITLE_KEYWORDS = [
    r"\bmanager\b",
    r"\bdirector\b",
    r"\badministrative\b",
    r"\bassistant\b",
    r"\bstrategist\b",
    r"\brecruiter\b",
    r"\bmarketing\b",
    r"\bhr\b",
    r"\blegal\b",
    r"\bdeveloper\b",
    r"\bfrontend\b",
    r"\bbackend\b",
    r"\bdevops\b",
    r"\bqa\b",
    r"\bsales\b"
]

REGEX_REQUIRED_3D = [re.compile(k, re.IGNORECASE) for k in REQUIRED_3D_KEYWORDS]
REGEX_EXCLUDED_TITLE = [re.compile(k, re.IGNORECASE) for k in EXCLUDED_TITLE_KEYWORDS]

HIST_FILE = BASE_DIR / "job_history.json"
if HIST_FILE.exists():
    try:
        with open(HIST_FILE, "r", encoding="utf-8") as f:
            SEEN_IDS = set(json.load(f))
    except Exception:
        SEEN_IDS = set()
else:
    SEEN_IDS = set()

def save_history():
    history_list = list(SEEN_IDS)[-2000:]
    with open(HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

def clean_html(raw_html: str) -> str:
    cleantext = re.sub(r'<[^>]+>', ' ', raw_html)
    cleantext = html.unescape(cleantext)
    return " ".join(cleantext.split())

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"User-Agent": "JobMonitor3DBot/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
        logging.info("📱 Alerta enviada con éxito a Telegram.")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def build_application_pitch() -> str:
    """Genera la plantilla de postulación directa en inglés lista para copiar con un toque."""
    pitch = (
        "Hi! I saw your call for 3D Art/Modeling. I'm a 3D Generalist specialized in Props, Characters, and Hard-Surface assets (Blender, ZBrush) with production experience in game/animation assets and 3D printing/collectibles.\n"
        f"You can check my portfolio here: {PORTFOLIO_URL}\n"
        "Available immediately for freelance/remote work. Looking forward to discussing how I can help with your project!"
    )
    return pitch

def is_strictly_3d_art(title: str, content: str) -> bool:
    """Filtra con precisión: descarta puestos corporativos y exige términos clave de arte 3D."""
    # 1. Descarte automático por título si contiene términos corporativos
    if any(r.search(title) for r in REGEX_EXCLUDED_TITLE):
        return False

    full_text = f"{title} {content}"

    # 2. Exclusión de candidatos que ofrecen sus servicios [For Hire] en Reddit
    title_lower = title.lower()
    if "[for hire]" in title_lower and "[hiring]" not in title_lower:
        return False

    # 3. Exigencia de coincidencia de al menos un término artístico 3D requerido
    has_3d_keyword = any(r.search(full_text) for r in REGEX_REQUIRED_3D)
    if not has_3d_keyword:
        return False

    return True

def fetch_feed(url: str):
    """Descarga el feed RSS con cabecera de navegador realista para evitar bloqueos 403."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()

def check_all_sources():
    logging.info("🔍 Comprobando feeds RSS con filtrado quirúrgico de Arte 3D...")
    new_found = 0

    for feed_info in FEEDS:
        name = feed_info["name"]
        url = feed_info["url"]

        try:
            feed_bytes = fetch_feed(url)
            parsed_feed = feedparser.parse(feed_bytes)

            for entry in parsed_feed.entries:
                item_id = entry.get("id", entry.get("link", ""))
                if not item_id or item_id in SEEN_IDS:
                    continue

                title = entry.get("title", "")
                summary = clean_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")

                if is_strictly_3d_art(title, summary):
                    new_found += 1
                    snippet = (summary[:200] + '...') if len(summary) > 200 else summary
                    pitch = build_application_pitch()

                    msg = (
                        f"🚨 <b>¡NUEVA OFERTA 3D DETECTADA!</b>\n\n"
                        f"📌 <b>Fuente:</b> {html.escape(name)}\n"
                        f"📝 <b>Puesto / Título:</b> {html.escape(title)}\n"
                        f"📄 <b>Resumen:</b> {html.escape(snippet)}\n\n"
                        f"🔗 <b>Enlace directo a la oferta:</b>\n{link}\n\n"
                        f"📋 <b>PROPUESTA RÁPIDA (Toca para copiar):</b>\n"
                        f"<code>{html.escape(pitch)}</code>"
                    )
                    send_telegram(msg)

                SEEN_IDS.add(item_id)

            # Pequeña pausa de cortesía entre feeds para no saturar servidores
            time.sleep(1)

        except Exception as e:
            logging.error(f"Error revisando {name}: {e}")

    if new_found > 0:
        save_history()
    logging.info(f"Comprobación finalizada. Ofertas válidas de Arte 3D enviadas: {new_found}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    logging.info("🤖 Job Monitor 3D Activo (Fuentes RSS ampliadas + Filtro quirúrgico)...")

    # Ejecutar primera revisión al iniciar
    check_all_sources()

    # Repetir revisión cada 5 minutos en local
    schedule.every(5).minutes.do(check_all_sources)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
