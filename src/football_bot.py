import requests
import os
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

FEEDS = [
    {"url": "https://fixturedownload.com/feed/json/epl-2025",                      "league": "Premier League",        "country": "אנגליה",   "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    {"url": "https://fixturedownload.com/feed/json/esp-primera-division-2025",     "league": "La Liga",               "country": "ספרד",     "flag": "🇪🇸"},
    {"url": "https://fixturedownload.com/feed/json/uefa-champions-league-2025",    "league": "Champions League",      "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/bundesliga-2025",               "league": "Bundesliga",            "country": "גרמניה",   "flag": "🇩🇪"},
    {"url": "https://fixturedownload.com/feed/json/serie-a-2025",                  "league": "Serie A",               "country": "איטליה",   "flag": "🇮🇹"},
    {"url": "https://fixturedownload.com/feed/json/ligue-1-2025",                  "league": "Ligue 1",               "country": "צרפת",     "flag": "🇫🇷"},
    {"url": "https://fixturedownload.com/feed/json/brasileiro-serie-a-2025",       "league": "Brasileirão Serie A",   "country": "ברזיל",    "flag": "🇧🇷"},
    {"url": "https://fixturedownload.com/feed/json/primera-division-argentina-2025","league": "Primera División",     "country": "ארגנטינה", "flag": "🇦🇷"},
    {"url": "https://fixturedownload.com/feed/json/la-liga-2025",                  "league": "La Liga",               "country": "ספרד",     "flag": "🇪🇸"},
    {"url": "https://fixturedownload.com/feed/json/champions-league-2025",         "league": "Champions League",      "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/europa-league-2025",            "league": "Europa League",         "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/conference-league-2025",        "league": "Conference League",     "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/super-lig-2025",                "league": "Süper Lig",             "country": "טורקיה",   "flag": "🇹🇷"},
    {"url": "https://fixturedownload.com/feed/json/primeira-liga-2025",            "league": "Primeira Liga",         "country": "פורטוגל",  "flag": "🇵🇹"},
    {"url": "https://fixturedownload.com/feed/json/copa-del-rey-2025",             "league": "Copa del Rey",          "country": "ספרד",     "flag": "🇪🇸"},
]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("נשלח!")
    except Exception as e:
        print(f"שגיאה בשליחה: {e}")


def fetch_all_fixtures():
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"Fetching fixtures for {today_str}...")
    all_fixtures = []

    for feed in FEEDS:
        try:
            response = requests.get(feed["url"], timeout=10)
            response.raise_for_status()
            matches = response.json()

            for m in matches:
                date_utc = m.get("DateUtc", "")
                if not date_utc.startswith(today_str):
                    continue

                try:
                    utc_dt = datetime.strptime(date_utc, "%Y-%m-%d %H:%M:%SZ")
                    time_str = (utc_dt + timedelta(hours=2)).strftime("%H:%M")
                except Exception:
                    time_str = "?"

                round_number = m.get("RoundNumber", "")
                stage_str = f"מחזור {round_number}" if round_number else ""

                all_fixtures.append({
                    "home": m.get("HomeTeam", "?"),
                    "away": m.get("AwayTeam", "?"),
                    "time": time_str,
                    "league": feed["league"],
                    "stage": stage_str,
                    "stadium": m.get("Location", ""),
                    "city": "",
                    "country": feed["country"],
                    "flag": feed["flag"],
                })

            print(f"{feed['league']}: found {sum(1 for m in matches if m.get('DateUtc','').startswith(today_str))} matches")

        except Exception as e:
            print(f"Error fetching {feed['league']}: {e}")

    print(f"Total fixtures: {len(all_fixtures)}")
    return all_fixtures


def analyze_with_claude(fixtures):
    if not fixtures:
        return []

    slim = [
        {"home": f["home"], "away": f["away"], "league": f["league"], "stage": f["stage"]}
        for f in fixtures
    ]

    prompt = f"""You are a football expert. Analyze these fixtures and classify each one.

hot = derbies, CL/EL knockouts, title deciders, top-of-table clashes between big clubs
interesting = big clubs, cup matches, notable games
regular = other matches

Always classify at least 3 matches as hot or interesting combined if there are enough matches.

Fixtures:
{json.dumps(slim, ensure_ascii=False)}

Return ONLY a JSON array with one object per fixture in the exact same order:
[{{"importance": "hot/interesting/regular", "reason": "short sentence in Hebrew explaining why to watch"}}]

No text outside the JSON array."""

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
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        response.raise_for_status()

        text = ""
        for block in response.json()["content"]:
            if block.get("type") == "text":
                text += block.get("text", "")

        text = text.strip()
        if "```" in text:
            start = text.find("[")
            end = text.rfind("]") + 1
            text = text[start:end]

        rankings = json.loads(text)
        print(f"Claude ranked {len(rankings)} matches")

        for i, fixture in enumerate(fixtures):
            if i < len(rankings):
                fixture["importance"] = rankings[i].get("importance", "regular")
                fixture["reason"] = rankings[i].get("reason", "")
            else:
                fixture["importance"] = "regular"
                fixture["reason"] = ""

        return fixtures

    except Exception as e:
        print(f"Claude error: {type(e).__name__}: {e}")
        for f in fixtures:
            f.setdefault("importance", "regular")
            f.setdefault("reason", "")
        return fixtures


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

    lines = [icon, f"{home} ✦ {away}", meta]
    if stadium or city:
        lines.append(f"📍 {', '.join(p for p in [stadium, city] if p)}")
    if reason:
        lines.append(f"◈ {reason}")

    return "\n".join(lines)


def send_daily_matches():
    print(f"Starting football bot for {date.today()}...")
    fixtures = fetch_all_fixtures()

    if not fixtures:
        send_telegram("לא נמצאו משחקים מעניינים היום 😴")
        return

    analyzed = analyze_with_claude(fixtures)

    order = {"hot": 0, "interesting": 1, "regular": 2}
    analyzed.sort(key=lambda m: order.get(m.get("importance", "regular"), 2))

    by_country = defaultdict(list)
    for m in analyzed:
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
