import requests
import os
import json
from collections import defaultdict
from datetime import datetime, date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("נשלח!")
    except Exception as e:
        print(f"שגיאה בשליחה: {e}")


def get_matches_from_claude():
    today = date.today().strftime("%d/%m/%Y")
    today_search = date.today().strftime("%Y-%m-%d")

    print(f"שולח בקשה ל-Claude עם web search...")

    prompt = f"""היום הוא {today}.

חפש ברשת את כל משחקי הכדורגל החשובים שמתקיימים היום {today_search}.

לאחר החיפוש, בחר את המשחקים הכי מעניינים ומדוברים - דרבים, ליגת אלופות, גביעים, קבוצות גדולות, משחקים מכריעים.
החזר לפחות 3 משחקים גם אם אין משחקים חמים במיוחד.

החזר JSON בלבד בפורמט הזה:
[
  {{
    "home": "שם קבוצת בית בעברית או אנגלית",
    "away": "שם קבוצת חוץ בעברית או אנגלית",
    "time": "HH:MM",
    "league": "שם הליגה בעברית",
    "stage": "שלב או מחזור - למשל: מחזור 28, שמינית גמר, גמר",
    "stadium": "שם האצטדיון",
    "city": "עיר",
    "country": "שם המדינה בעברית",
    "flag": "אמוג'י דגל המדינה",
    "reason": "משפט קצר בעברית למה כדאי לצפות",
    "importance": "hot/interesting/regular"
  }}
]

כללים:
- hot = דרבים, נוקאאוט CL, משחקים מכריעים לאליפות
- interesting = קבוצות גדולות, גביעים, משחקים מעניינים
- regular = שאר המשחקים הראויים לציון
- השעות בשעון ישראל (UTC+2)
- החזר JSON בלבד ללא טקסט נוסף"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 4000,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        print(f"סטטוס: {response.status_code}")
        response.raise_for_status()

        content = response.json()["content"]
        text = ""
        for block in content:
            if block.get("type") == "text":
                text += block.get("text", "")

        print(f"תגובה מ-Claude: {text[:300]}")

        text = text.strip()
        if "```" in text:
            start = text.find("[")
            end = text.rfind("]") + 1
            text = text[start:end]

        matches = json.loads(text)
        print(f"Claude מצא {len(matches)} משחקים!")
        return matches

    except requests.exceptions.HTTPError as e:
        print(f"שגיאת HTTP: {e} | {e.response.text[:200]}")
        return []
    except Exception as e:
        print(f"שגיאה: {type(e).__name__}: {e}")
        return []


def format_match(match):
    home = match.get("home", "?")
    away = match.get("away", "?")
    time_str = match.get("time", "?")
    league = match.get("league", "")
    stage = match.get("stage", "")
    stadium = match.get("stadium", "")
    city = match.get("city", "")
    reason = match.get("reason", "")
    importance = match.get("importance", "regular")

    icon = "🔥" if importance == "hot" else "⭐"
    meta = " | ".join(p for p in [league, stage, time_str] if p)

    lines = [
        icon,
        f"{home} ✦ {away}",
        meta,
    ]
    if stadium or city:
        lines.append(f"📍 {', '.join(p for p in [stadium, city] if p)}")
    if reason:
        lines.append(f"◈ {reason}")

    return "\n".join(lines)


def send_daily_matches():
    print(f"מחפש משחקים ל-{date.today()}...")
    matches = get_matches_from_claude()

    if not matches:
        send_telegram("לא נמצאו משחקים מעניינים היום 😴")
        return

    order = {"hot": 0, "interesting": 1, "regular": 2}
    matches.sort(key=lambda m: order.get(m.get("importance", "regular"), 2))

    by_country = defaultdict(list)
    for m in matches:
        key = (m.get("flag", "🌍"), m.get("country", "אחר"))
        by_country[key].append(m)

    today_str = date.today().strftime("%d/%m/%Y")
    parts = [
        "╔═══════════════════════════╗",
        f"⚽ משחקי היום • {today_str}",
        "╚═══════════════════════════╝",
    ]

    for (flag, country), country_matches in by_country.items():
        parts.append(f"\n{flag} {country}")
        parts.append("──────────────────────────")
        for m in country_matches:
            parts.append("")
            parts.append(format_match(m))

    send_telegram("\n".join(parts))


if __name__ == "__main__":
    send_daily_matches()
