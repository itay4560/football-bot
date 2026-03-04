# Football Bot

A Telegram bot that sends a daily summary of the most interesting football matches, powered by Claude AI with web search.

## How It Works

Every day at 06:00 UTC, the bot:
1. Asks Claude to search the web for today's football matches
2. Categorizes them as **Hot** (derbies, CL knockouts), **Interesting** (big clubs, cups), or **Regular**
3. Sends a formatted message to a Telegram chat

## Project Structure

```
football-bot/
├── src/
│   └── football_bot.py   # Main bot logic
├── docs/
│   └── README.md         # This file
├── .env.example          # Required environment variables
├── .gitignore
└── requirements.txt
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/itay4560/football-bot.git
cd football-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Your Telegram bot token (from @BotFather) |
| `CHAT_ID` | The Telegram chat ID to send messages to |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

### 4. Run manually

```bash
python src/football_bot.py
```

## Automated Runs (GitHub Actions)

The bot runs automatically every day via GitHub Actions (`.github/workflows/daily.yml`).

Add your secrets under **GitHub repo → Settings → Secrets and variables → Actions**.
