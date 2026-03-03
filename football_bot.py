import requests
import os
import json
from datetime import datetime, date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

FOOTBALL_API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

COMPETITIONS = {
    "PL": "פרמייר ליג",
    "PD": "לה ליגה",
    "CL": "ליגת האלופות",
    "FL1": "ליג 1",
    "BL1": "בונדסליגה",
    "SA": "סריה א",
    "EL": "ליגה אירופית",
}

STADIUM_CITIES = {
    "Old Trafford": "מנצ'סטר",
    "Etihad Stadium": "מנצ'סטר",
    "Anfield": "ליברפול",
    "Emirates Stadium": "לונדון",
    "Stamford Bridge": "לונדון",
    "Tottenham Hotspur Stadium": "לונדון",
    "Camp Nou": "ברצלונה",
    "Estadi Olimpic Lluis Companys": "ברצלונה",
    "Santiago Bernabeu": "מדריד",
    "Wanda Metropolitano": "מדריד",
    "Signal Iduna Park": "דורטמונד",
    "Allianz Arena": "מינכן",
    "San Siro": "מילאנו",
    "Parc des Princes": "פריז",
    "Molineux Stadium": "וולברהמפטון",
    "Goodison Park": "ליברפול",
    "Vitality Stadium": "בורנמות'",
    "Elland Road": "לידס",
    "London Stadium": "לונדון",
    "Villa Park": "בירמינגהם",
}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("נשלח!")
    except Exception as e:
        print(f"שגיאה בשליחה: {e}")


def get_matches_today():
    today = date.today().strftime("%Y-%m-%d")
    all_matches = []
    for code, name in COMPETITIONS.items():
        try:
            url = f"{FOOTBALL_API_URL}/competitions/{code}/matches"
            params = {"dateFrom": today, "dateTo": today}
            res = requests.get(url, headers=HEADERS, params=params)
            if res.status_code == 200:
                matches = res.json().get("matches", [])
                for m in matches:
                    m["competition_name"] = name
                    m["competition_code"] = code
                all_matches.extend(matches)
        except Exception as e:
            print(f"שגיאה ב-{code}: {e}")
    return all_matches


def format_time(utc_time):
    try:
        dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ")
        hour = (dt.hour + 2) % 24
        return f"{hour:02d}:{dt.minute:02d}"
    except Exception:
        return "?"


def analyze_with_claude(matches):
    if not matches:
        return []

    print(f"שולח {len(matches)} משחקים ל-Claude לניתוח...")

    if not ANTHROPIC_API_KEY:
        print("שגיאה: ANTHROPIC_API_KEY לא מוגדר!")
        return []

    matches_list = []
    for i, m in enumerate(matches):
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        comp = m.get("competition_name", "")
        stage = m.get("stage", "")
        matchday = m.get("matchday", "")
        time_str = format_time(m.get("utcDate", ""))
        matches_list.append(f"{i}. {home} vs {away} | {comp} | שלב: {stage} | מחזור: {matchday} | {time_str}")

    matches_text = "\n".join(matches_list)

    prompt = f"""אתה מומחה כדורגל. להלן משחקי היום:

{matches_text}

עבור כל משחק החזר JSON בפורמט הבא (מערך):
[
  {{
    "index": 0,
    "score": 8,
    "reason": "משפט קצר בעברית למה שווה לראות",
    "must_watch": true
  }}
]

חוקים:
- score 8-10 = חייב לראות (דרבים, נוקאאוט, משחקים מכריעים, קבוצות גדולות)
- score 5-7 = מעניין
- score 1-4 = רגיל
- must_watch = true רק ל-score 7 ומעלה
- החזר JSON בלבד ללא שום טקסט נוסף"""

    try:
        print("קורא ל-Claude API...")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        print(f"סטטוס תגובה: {response.status_code}")
        response.raise_for_status()
        text = response.json()["content"][0]["text"].strip()
        print(f"תגובה מ-Claude: {text[:200]}")
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])
        analysis = json.loads(text)
        print(f"Claude ניתח {len(analysis)} משחקים בהצלחה!")
        return analysis
    except requests.exceptions.HTTPError as e:
        print(f"שגיאת HTTP מ-Claude: {e} | תגובה: {e.response.text}")
        return []
    except Exception as e:
        print(f"שגיאה ב-Claude: {type(e).__name__}: {e}")
        return []


def format_match(match, reason=""):
    home = match.get("homeTeam", {}).get("name", "?")
    away = match.get("awayTeam", {}).get("name", "?")
    comp = match.get("competition_name", "")
    venue = match.get("venue", "")
    time_str = format_time(match.get("utcDate", ""))
    city = STADIUM_CITIES.get(venue, "")

    lines = ["", f"<b>{home} vs {away}</b>", f"שעה: {time_str} (ישראל)", f"ליגה: {comp}"]
    if venue:
        lines.append(f"אצטדיון: {venue}{', ' + city if city else ''}")
    if reason:
        lines.append(f"למה לצפות: {reason}")
    return "\n".join(lines)


def send_daily_matches():
    print(f"מחפש משחקים ל-{date.today()}...")
    matches = get_matches_today()
    print(f"נמצאו {len(matches)} משחקים")

    analysis = analyze_with_claude(matches)
    analysis_map = {item["index"]: item for item in analysis}

    must_watch = []
    interesting = []
    regular = []

    for i, match in enumerate(matches):
        info = analysis_map.get(i, {})
        score = info.get("score", 3)
        reason = info.get("reason", "")
        must = info.get("must_watch", False)

        if must or score >= 7:
            must_watch.append((match, reason))
        elif score >= 5:
            interesting.append((match, reason))
        else:
            regular.append((match, ""))

    today_str = date.today().strftime("%d/%m/%Y")
    message_parts = [f"<b>משחקי כדורגל היום - {today_str}</b>"]

    if must_watch:
        message_parts.append(f"\n🔥 <b>חייב לראות ({len(must_watch)}):</b>")
        message_parts.append("━━━━━━━━━━━━━━━")
        for match, reason in must_watch:
            message_parts.append(format_match(match, reason))

    if interesting:
        message_parts.append(f"\n⭐ <b>מעניין ({len(interesting)}):</b>")
        message_parts.append("━━━━━━━━━━━━━━━")
        for match, reason in interesting:
            message_parts.append(format_match(match, reason))

    if regular:
        message_parts.append(f"\n📋 <b>שאר המשחקים ({len(regular)}):</b>")
        message_parts.append("━━━━━━━━━━━━━━━")
        for match, _ in regular[:6]:
            message_parts.append(format_match(match, ""))

    if not matches:
        message_parts.append("\nאין משחקים היום")

    send_telegram("\n".join(message_parts))


if __name__ == "__main__":
    send_daily_matches()
