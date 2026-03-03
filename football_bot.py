import requests
import schedule
import time
from datetime import datetime, date

TELEGRAM_TOKEN = "8638543906:AAGlksfwuGK4TKVmmVoxkrovki3MA7BO1Qo"
CHAT_ID = "651797514"
FOOTBALL_API_KEY = "7c100e549ff047b1bd17b1838b2fe545"
FOOTBALL_API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

COMPETITIONS = {"PL": "Premier League","PD": "La Liga","CL": "Champions League","FL1": "Ligue 1","BL1": "Bundesliga","SA": "Serie A"}
RIVALRIES = [
    {"teams": ["Manchester City", "Manchester United"], "name": "Manchester Derby"},
    {"teams": ["Arsenal", "Tottenham Hotspur"], "name": "North London Derby"},
    {"teams": ["Liverpool", "Manchester United"], "name": "Northwest Derby"},
    {"teams": ["Liverpool", "Everton"], "name": "Merseyside Derby"},
    {"teams": ["Real Madrid CF", "FC Barcelona"], "name": "El Clasico"},
    {"teams": ["Real Madrid CF", "Club Atletico de Madrid"], "name": "Madrid Derby"},
    {"teams": ["AC Milan", "FC Internazionale Milano"], "name": "Derby della Madonnina"},
    {"teams": ["AS Roma", "SS Lazio"], "name": "Derby della Capitale"},
]
ISRAELI_TEAMS = ["Maccabi Tel Aviv", "Hapoel Tel Aviv", "Maccabi Haifa", "Beitar Jerusalem"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}).raise_for_status()
    except Exception as e:
        print(f"Error: {e}")

def get_matches_today():
    today = date.today().strftime("%Y-%m-%d")
    all_matches = []
    for code, name in COMPETITIONS.items():
        try:
            res = requests.get(f"{FOOTBALL_API_URL}/competitions/{code}/matches", headers=HEADERS, params={"dateFrom": today, "dateTo": today})
            if res.status_code == 200:
                for m in res.json().get("matches", []):
                    m["competition_name"] = name
                    m["competition_code"] = code
                    all_matches.append(m)
        except Exception as e:
            print(f"Error {code}: {e}")
    return all_matches

def is_must_watch(match):
    home = match.get("homeTeam", {}).get("name", "")
    away = match.get("awayTeam", {}).get("name", "")
    stage = match.get("stage", "")
    matchday = match.get("matchday", 0) or 0
    competition = match.get("competition_code", "")
    reasons = []
    if competition == "CL":
        reasons.append("Champions League Knockout!" if stage in ["LAST_16","QUARTER_FINALS","SEMI_FINALS","FINAL"] else "Champions League")
    for r in RIVALRIES:
        if any(t in home for t in r["teams"]) and any(t in away for t in r["teams"]):
            reasons.append(r["name"])
            break
    if any(t in home or t in away for t in ISRAELI_TEAMS):
        reasons.append("Israeli team!")
    if stage in ["FINAL", "SEMI_FINALS"]:
        reasons.append("Final!")
    if competition in ["PL","PD"] and matchday >= 33:
        reasons.append("Critical matchday!")
    return reasons

def format_match(match, reasons):
    home = match.get("homeTeam",{}).get("name","?")
    away = match.get("awayTeam",{}).get("name","?")
    comp = match.get("competition_name","")
    venue = match.get("venue","")
    try:
        dt = datetime.strptime(match.get("utcDate",""), "%Y-%m-%dT%H:%M:%SZ")
        time_str = f"{(dt.hour+2)%24:02d}:{dt.minute:02d}"
    except:
        time_str = "?"
    lines = [f"", f"<b>{home} vs {away}</b>", f"Time: {time_str} (Israel)", f"League: {comp}"]
    if venue: lines.append(f"Stadium: {venue}")
    if reasons: lines.append(f"WHY WATCH: {' | '.join(reasons)}")
    return "\n".join(lines)

def send_daily_matches():
    matches = get_matches_today()
    must_watch = [(m, is_must_watch(m)) for m in matches if is_must_watch(m)]
    regular = [(m, []) for m in matches if not is_must_watch(m)]
    today_str = date.today().strftime("%d/%m/%Y")
    parts = [f"<b>Football Today - {today_str}</b>"]
    if must_watch:
        parts.append(f"\n<b>MUST WATCH ({len(must_watch)}):</b>")
        for match, reasons in must_watch:
            parts.append(format_match(match, reasons))
    if regular:
        parts.append(f"\n<b>Other games ({len(regular)}):</b>")
        for match, _ in regular[:8]:
            parts.append(format_match(match, []))
    if not must_watch and not regular:
        parts.append("No games today")
    send_telegram("\n".join(parts))

def main():
    print("Bot started!")
    send_daily_matches()
    schedule.every().day.at("08:00").do(send_daily_matches)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
