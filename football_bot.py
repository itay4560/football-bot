import requests
import os
from datetime import datetime, date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")

FOOTBALL_API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

COMPETITIONS = {
        "PL": "🏴 פרמייר ליג",
        "PD": "🇪🇸 לה ליגה",
        "CL": "🏆 ליגת האלופות",
        "FL1": "🇫🇷 ליג 1",
        "BL1": "🇩🇪 בונדסליגה",
        "SA": "🇮🇹 סריה א",
        "EL": "🟠 ליגה אירופית",
}

RIVALRIES = [
        {"teams": ["Manchester City FC", "Manchester United FC"], "name": "🔴🔵 דרבי מנצ'סטר"},
        {"teams": ["Arsenal FC", "Tottenham Hotspur FC"], "name": "🔴⚪ דרבי צפון לונדון"},
        {"teams": ["Arsenal FC", "Chelsea FC"], "name": "🔴🔵 דרבי לונדון"},
        {"teams": ["Liverpool FC", "Manchester United FC"], "name": "🔴 נורת'ווסט דרבי"},
        {"teams": ["Liverpool FC", "Everton FC"], "name": "🔵🔴 דרבי מרסיסייד"},
        {"teams": ["Chelsea FC", "Tottenham Hotspur FC"], "name": "🔵⚪ דרבי לונדון"},
        {"teams": ["Real Madrid CF", "FC Barcelona"], "name": "👑 אל קלאסיקו 🔥"},
        {"teams": ["Real Madrid CF", "Atletico de Madrid"], "name": "⚪🔴 דרבי מדריד"},
        {"teams": ["FC Barcelona", "Atletico de Madrid"], "name": "🔵🔴 דרבי ספרד"},
        {"teams": ["Juventus FC", "FC Internazionale Milano"], "name": "⚫⚪ דרבי ד'איטליה"},
        {"teams": ["AS Roma", "SS Lazio"], "name": "🟡🔴 דרבי רומא"},
        {"teams": ["AC Milan", "FC Internazionale Milano"], "name": "🔴⚫ דרבי מילאנו"},
        {"teams": ["Borussia Dortmund", "FC Bayern München"], "name": "🟡⚫ קלאסיקר גרמני"},
]

ISRAELI_TEAMS = ["Maccabi Tel Aviv", "Hapoel Tel Aviv", "Maccabi Haifa", "Beitar Jerusalem", "Hapoel Beer Sheva"]

def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": messagimport requests
    import os
from datetime import datetime, date

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")

FOOTBALL_API_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

COMPETITIONS = {
        "PL": "🏴 פרמייר ליג",
        "PD": "🇪🇸 לה ליגה",
        "CL": "🏆 ליגת האלופות",
        "FL1": "🇫🇷 ליג 1",
        "BL1": "🇩🇪 בונדסליגה",
        "SA": "🇮🇹 סריה א",
        "EL": "🟠 ליגה אירופית",
}

RIVALRIES = [
        {"teams": ["Manchester City FC", "Manchester United FC"], "name": "🔴🔵 דרבי מנצ'סטר"},
        {"teams": ["Arsenal FC", "Tottenham Hotspur FC"], "name": "🔴⚪ דרבי צפון לונדון"},
        {"teams": ["Arsenal FC", "Chelsea FC"], "name": "🔴🔵 דרבי לונדון"},
        {"teams": ["Liverpool FC", "Manchester United FC"], "name": "🔴 נורת'ווסט דרבי"},
        {"teams": ["Liverpool FC", "Everton FC"], "name": "🔵🔴 דרבי מרסיסייד"},
        {"teams": ["Chelsea FC", "Tottenham Hotspur FC"], "name": "🔵⚪ דרבי לונדון"},
        {"teams": ["Real Madrid CF", "FC Barcelona"], "name": "👑 אל קלאסיקו 🔥"},
        {"teams": ["Real Madrid CF", "Atletico de Madrid"], "name": "⚪🔴 דרבי מדריד"},
        {"teams": ["FC Barcelona", "Atletico de Madrid"], "name": "🔵🔴 דרבי ספרד"},
        {"teams": ["Juventus FC", "FC Internazionale Milano"], "name": "⚫⚪ דרבי ד'איטליה"},
        {"teams": ["AS Roma", "SS Lazio"], "name": "🟡🔴 דרבי רומא"},
        {"teams": ["AC Milan", "FC Internazionale Milano"], "name": "🔴⚫ דרבי מילאנו"},
        {"teams": ["Borussia Dortmund", "FC Bayern München"], "name": "🟡⚫ קלאסיקר גרמני"},
]

ISRAELI_TEAMS = ["Maccabi Tel Aviv", "Hapoel Tel Aviv", "Maccabi Haifa", "Beitar Jerusalem", "Hapoel Beer Sheva"]

def send_telegram(message):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        try:
                    response = requests.post(url, data=data)
                    response.raise_for_status()
                    print("✅ הודעה נשלחה!")
except Exception as e:
        print(f"❌ שגיאה: {e}")

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
                                    print(f"שגיאה בליגה {code}: {e}")
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
                                    reasons.append("🏆 נוקאאוט ליגת האלופות!")
        else:
                        reasons.append("🏆 ליגת האלופות")
                for rivalry in RIVALRIES:
                            teams = rivalry["teams"]
                            if any(t in home for t in teams) and any(t in away for t in teams):
                                            reasons.append(rivalry["name"])
                                            break
                                    for team in ISRAELI_TEAMS:
                                                if team in home or team in away:
                                                                reasons.append("🇮🇱 קבוצה ישראלית!")
                                                                break
                                                        if stage in ["FINAL", "SEMI_FINALS"]:
                                                                    reasons.append("🏅 גמר / חצי גמר!")
                                                                if competition in ["PL", "PD"] and matchday >= 33:
                                                                            reasons.append("🔥 מחזור קריטי!")
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
    ex
