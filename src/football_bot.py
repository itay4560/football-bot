import requests
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

CUP_LEAGUES = {
    "Champions League", "Europa League", "Conference League", "Copa del Rey",
}

FEEDS = [
    {"url": "https://fixturedownload.com/feed/json/epl-2025",                      "league": "Premier League",        "country": "אנגליה",   "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    {"url": "https://fixturedownload.com/feed/json/bundesliga-2025",               "league": "Bundesliga",            "country": "גרמניה",   "flag": "🇩🇪"},
    {"url": "https://fixturedownload.com/feed/json/serie-a-2025",                  "league": "Serie A",               "country": "איטליה",   "flag": "🇮🇹"},
    {"url": "https://fixturedownload.com/feed/json/ligue-1-2025",                  "league": "Ligue 1",               "country": "צרפת",     "flag": "🇫🇷"},
    {"url": "https://fixturedownload.com/feed/json/la-liga-2025",                  "league": "La Liga",               "country": "ספרד",     "flag": "🇪🇸"},
    {"url": "https://fixturedownload.com/feed/json/champions-league-2025",         "league": "Champions League",      "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/europa-league-2025",            "league": "Europa League",         "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/conference-league-2025",        "league": "Conference League",     "country": "אירופה",   "flag": "🌍"},
    {"url": "https://fixturedownload.com/feed/json/super-lig-2025",                "league": "Süper Lig",             "country": "טורקיה",   "flag": "🇹🇷"},
    {"url": "https://fixturedownload.com/feed/json/primeira-liga-2025",            "league": "Primeira Liga",         "country": "פורטוגל",  "flag": "🇵🇹"},
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
                    "country": feed["country"],
                    "flag": feed["flag"],
                })

            print(f"{feed['league']}: found {sum(1 for m in matches if m.get('DateUtc','').startswith(today_str))} matches")

        except Exception as e:
            print(f"Error fetching {feed['league']}: {e}")

    print(f"Total fixtures: {len(all_fixtures)}")
    return all_fixtures


def format_match(match):
    home = match.get("home", "?")
    away = match.get("away", "?")
    time_str = match.get("time", "?")
    league = match.get("league", "")
    stage = match.get("stage", "")
    stadium = match.get("stadium", "")

    meta = " | ".join(p for p in [league, stage, time_str] if p)

    lines = [f"⚽ {home} ✦ {away}", meta]
    if stadium:
        lines.append(f"📍 {stadium}")

    return "\n".join(lines)


def send_daily_matches():
    print(f"Starting football bot for {date.today()}...")
    fixtures = fetch_all_fixtures()

    if not fixtures:
        send_telegram("לא נמצאו משחקים היום 😴")
        return

    by_country = defaultdict(list)
    for m in fixtures:
        key = (m.get("flag", "🌍"), m.get("country", "אחר"))
        by_country[key].append(m)

    today_str = date.today().strftime("%d/%m/%Y")
    parts = [
        "╔═══════════════════════════╗",
        f"⚽ משחקי היום • {today_str}",
        "╚═══════════════════════════╝",
    ]

    for (flag, country), country_matches in by_country.items():
        league_matches = [m for m in country_matches if m.get("league") not in CUP_LEAGUES]
        cup_matches = [m for m in country_matches if m.get("league") in CUP_LEAGUES]

        parts.append(f"\n{flag} {country}")
        parts.append("──────────────────────────")

        for m in league_matches:
            parts.append("")
            parts.append(format_match(m))

        if cup_matches:
            if league_matches:
                parts.append("\n🏆 גביע:")
            for m in cup_matches:
                parts.append("")
                parts.append(format_match(m))

    send_telegram("\n".join(parts))


if __name__ == "__main__":
    send_daily_matches()
