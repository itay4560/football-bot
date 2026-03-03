import requests
import os
from datetime import datetime, date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")

FOOTBALL_API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

COMPETITIONS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "CL": "Champions League",
    "FL1": "Ligue 1",
    "BL1": "Bundesliga",
    "SA": "Serie A",
}

RIVALRIES = [
    {"teams": ["Manchester City FC", "Manchester United FC"], "name": "Manchester Derby"},
    {"teams": ["Arsenal FC", "Tottenham Hotspur FC"], "name": "North London Derby"},
    {"teams": ["Liverpool FC", "Manchester United FC"], "name": "NorthWest Derby"},
    {"teams": ["Liverpool FC", "Everton FC"], "name": "Merseyside Derby"},
    {"teams": ["Chelsea FC", "Tottenham Hotspur FC"], "name": "London Derby"},
    {"teams": ["Arsenal FC", "Chelsea FC"], "name": "London Derby"},
    {"teams": ["Real Madrid CF", "FC Barcelona"], "name": "El Clasico"},
    {"teams": ["Real Madrid CF", "Atletico de Madrid"], "name": "Madrid Derby"},
    {"teams": ["AC Milan", "FC Internazionale Milano"], "name": "Derby Milano"},
    {"teams": ["AS Roma", "SS Lazio"], "name": "Derby Roma"},
    {"teams": ["Borussia Dortmund", "FC Bayern Munchen"], "name": "Der Klassiker"},
]

BIG_TEAMS = [
    "Liverpool FC", "Arsenal FC", "Manchester City FC", "Manchester United FC",
    "Chelsea FC", "Tottenham Hotspur FC", "FC Barcelona", "Real Madrid CF",
    "Atletico de Madrid", "FC Bayern Munchen", "Borussia Dortmund",
    "Juventus FC", "AC Milan", "FC Internazionale Milano", "Paris Saint-Germain FC",
]

ISRAELI_TEAMS = ["Maccabi Tel Aviv", "Hapoel Tel Aviv", "Maccabi Haifa", "Beitar Jerusalem", "Hapoel Beer Sheva"]

STADIUM_CITIES = {
    "Old Trafford": "Manchester",
    "Etihad Stadium": "Manchester",
    "Anfield": "Liverpool",
    "Emirates Stadium": "London",
    "Stamford Bridge": "London",
    "Tottenham Hotspur Stadium": "London",
    "Camp Nou": "Barcelona",
    "Santiago Bernabeu": "Madrid",
    "Wanda Metropolitano": "Madrid",
    "Signal Iduna Park": "Dortmund",
    "Allianz Arena": "Munich",
    "San Siro": "Milan",
    "Juventus Stadium": "Turin",
    "Parc des Princes": "Paris",
    "Molineux Stadium": "Wolverhampton",
    "Goodison Park": "Liverpool",
    "Vitality Stadium": "Bournemouth",
    "Brentford Community Stadium": "London",
    "Elland Road": "Leeds",
    "Stadium of Light": "Sunderland",
}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("Message sent!")
    except Exception as e:
        print(f"Error: {e}")


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
            print(f"Error in {code}: {e}")
    return all_matches


def is_must_watch(match):
    home = match.get("homeTeam", {}).get("name", "")
    away = match.get("awayTeam", {}).get("name", "")
    stage = match.get("stage", "")
    matchday = match.get("matchday", 0) or 0
    competition = match.get("competition_code", "")
    reasons = []

    if competition == "CL":
        if stage in ["LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "FINAL"]:
            reasons.append("Champions League Knockout!")
        else:
            reasons.append("Champions League")

    for rivalry in RIVALRIES:
        teams = rivalry["teams"]
        if any(t in home for t in teams) and any(t in away for t in teams):
            reasons.append(rivalry["name"])
            break

    for team in ISRAELI_TEAMS:
        if team in home or team in away:
            reasons.append("Israeli team!")
            break

    if stage in ["FINAL", "SEMI_FINALS"]:
        reasons.append("Final / Semi Final!")

    if competition in ["PL", "PD"] and matchday >= 33:
        reasons.append("Critical matchday!")

    home_big = any(t in home for t in BIG_TEAMS)
    away_big = any(t in away for t in BIG_TEAMS)
    if (home_big or away_big) and competition in ["PL", "PD", "CL", "BL1", "SA"]:
        reasons.append("Big team match!")

    return reasons


def format_match(match, reasons):
    home = match.get("homeTeam", {}).get("name", "?")
    away = match.get("awayTeam", {}).get("name", "?")
    comp = match.get("competition_name", "")
    venue = match.get("venue", "")
    utc_time = match.get("utcDate", "")

    try:
        dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ")
        hour = (dt.hour + 2) % 24
        time_str = f"{hour:02d}:{dt.minute:02d}"
    except Exception:
        time_str = "?"

    city = STADIUM_CITIES.get(venue, "")

    lines = ["", f"<b>{home} vs {away}</b>", f"Time: {time_str} (Israel)"]
    if venue:
        if city:
            lines.append(f"Stadium: {venue}, {city}")
        else:
            lines.append(f"Stadium: {venue}")
    lines.append(f"League: {comp}")
    if reasons:
        lines.append(f"Why watch: {' | '.join(reasons)}")
    return "\n".join(lines)


def send_daily_matches():
    print(f"Searching matches for {date.today()}...")
    matches = get_matches_today()
    must_watch = []
    regular = []

    for match in matches:
        reasons = is_must_watch(match)
        if reasons:
            must_watch.append((match, reasons))
        else:
            regular.append((match, []))

    today_str = date.today().strftime("%d/%m/%Y")
    message_parts = [f"<b>Football Today - {today_str}</b>"]

    if must_watch:
        message_parts.append(f"\nMust Watch ({len(must_watch)} games):")
        message_parts.append("---------------")
        for match, reasons in must_watch:
            message_parts.append(format_match(match, reasons))

    if regular:
        message_parts.append(f"\nOther games ({len(regular)}):")
        message_parts.append("---------------")
        for match, _ in regular[:8]:
            message_parts.append(format_match(match, []))

    if not must_watch and not regular:
        message_parts.append("\nNo interesting matches today")

    send_telegram("\n".join(message_parts))


if __name__ == "__main__":
    send_daily_matches()
