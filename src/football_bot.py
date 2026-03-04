import requests
import os
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")

COMPETITIONS = "PL,PD,CL,BL1,SA,FL1,DED,PPL,EL,ECL"

COUNTRY_MAP = {
    "England":     ("אנגליה",    "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "Spain":       ("ספרד",      "🇪🇸"),
    "Germany":     ("גרמניה",    "🇩🇪"),
    "Italy":       ("איטליה",    "🇮🇹"),
    "France":      ("צרפת",      "🇫🇷"),
    "Netherlands": ("הולנד",     "🇳🇱"),
    "Portugal":    ("פורטוגל",   "🇵🇹"),
    "Europe":      ("אירופה",    "🌍"),
    "World":       ("אירופה",    "🌍"),
}

STAGE_MAP = {
    "GROUP_STAGE":              "שלב הבתים",
    "ROUND_OF_16":              "שמינית גמר",
    "LAST_16":                  "שמינית גמר",
    "QUARTER_FINALS":           "רבע גמר",
    "SEMI_FINALS":              "חצי גמר",
    "FINAL":                    "גמר",
    "KNOCKOUT_PHASE_PLAY_OFFS": "פלייאוף",
    "PLAYOFF_ROUND_ONE":        "פלייאוף",
    "PLAYOFF_ROUND_TWO":        "פלייאוף",
}

SKIP_STATUSES = {"POSTPONED", "SUSPENDED", "CANCELLED"}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("נשלח!")
    except Exception as e:
        print(f"שגיאה בשליחה: {e}")


def fetch_fixtures():
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"Fetching fixtures for {today_str}...")
    try:
        response = requests.get(
            "https://api.football-data.org/v4/matches",
            headers={"X-Auth-Token": FOOTBALL_API_KEY},
            params={"dateFrom": today_str, "dateTo": today_str, "competitions": COMPETITIONS},
            timeout=15,
        )
        print(f"Status: {response.status_code}")
        print(f"Response (first 500 chars): {response.text[:500]}")
        response.raise_for_status()
        matches = response.json().get("matches", [])
        print(f"Found {len(matches)} fixtures")
        return matches
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return []


def parse_fixtures(raw):
    fixtures = []
    for m in raw:
        if m.get("status") in SKIP_STATUSES:
            continue

        home = m.get("homeTeam", {}).get("shortName") or m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("shortName") or m.get("awayTeam", {}).get("name", "?")
        competition = m.get("competition", {}).get("name", "")
        area_name = m.get("area", {}).get("name", "Europe")
        stage = m.get("stage", "REGULAR_SEASON")
        matchday = m.get("matchday")

        stage_str = STAGE_MAP.get(stage, "")
        if not stage_str and matchday:
            stage_str = f"מחזור {matchday}"

        utc_date = m.get("utcDate", "")
        try:
            utc_dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
            time_str = (utc_dt + timedelta(hours=2)).strftime("%H:%M")
        except Exception:
            time_str = "?"

        country, flag = COUNTRY_MAP.get(area_name, ("אירופה", "🌍"))

        fixtures.append({
            "home": home,
            "away": away,
            "time": time_str,
            "league": competition,
            "stage": stage_str,
            "stadium": "",
            "city": "",
            "country": country,
            "flag": flag,
        })

    return fixtures


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
    raw = fetch_fixtures()
    fixtures = parse_fixtures(raw)

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
