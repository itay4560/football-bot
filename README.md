# Football Bot

A Telegram bot that sends a daily summary of the most interesting football matches, powered by Claude AI with web search.

## How It Works

Every day at 08:30 UTC, the bot:
1. Searches the web for today's football matches
2. Categorizes them as:
   - 🔥 **Hot** - Derbies, Champions League knockouts
      - ⭐ **Interesting** - Big clubs, cup matches
         - ⚽ **Regular** - Other matches
         3. Sends a formatted summary to a Telegram chat

         ## Setup

         1. Clone the repo
         ```
         git clone https://github.com/itay4560/football-bot.git
         ```

         2. Install dependencies
         ```
         pip install -r requirements.txt
         ```

         3. Set environment variables - copy `.env.example` to `.env` and fill in:

         | Variable | Description |
         |---|---|
         | TELEGRAM_TOKEN | Your Telegram bot token (from @BotFather) |
         | CHAT_ID | The Telegram chat ID to send messages to |
         | ANTHROPIC_API_KEY | Your Anthropic API key |

         4. Run manually
         ```
         python src/football_bot.py
         ```

         ## Automated Runs

         The bot runs automatically every day via GitHub Actions. Add your secrets under:
         `GitHub repo → Settings → Secrets and variables → Actions`

         ## Built With
         - Python
         - Telegram Bot API
         - Claude AI (Anthropic)
         - GitHub Actions
