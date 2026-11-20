# 🔔 Ringo Bot

### A smarter way to keep your Discord community on schedule.

**Custom Reminders · DISBOARD Bump Tracking · Persistent Scheduling**

**Tech Stack:** Python · discord.py · SQLite · python-dotenv

Built for the **Reader's Delight** Discord community, Ringo makes it easier for moderators to schedule announcements, manage reminders, and stay on top of DISBOARD bumps.

## ✨ Features

- **Slash-command management** — Create, list, and delete reminders directly in Discord.
- **Flexible scheduling** — Configure intervals in minutes, hours, or days, up to 90 days.
- **One-time and recurring reminders** — Send messages once or on a repeating schedule.
- **DISBOARD integration** — Detect successful bump confirmations and reset a two-hour timer.
- **Custom notifications** — Send themed embeds and a custom bump banner.
- **SQLite persistence** — Save reminders across bot restarts.
- **Moderator permissions** — Restrict management to users with Manage Server permission.
- **Multi-server support** — Manage up to five reminders per Discord server.

## 🖥️ Commands

| Command | Function |
|---|---|
| `/reminder-create` | Create a reminder with a message, channel, interval, and looping option |
| `/reminder-list` | Display scheduled reminders and their next notification times |
| `/reminder-delete` | Delete an existing reminder after confirmation |

## 🚀 Installation

**1. Clone the repository**

```bash
git clone https://github.com/HIRGON7/Ringo-Bot.git
cd Ringo-Bot
```

**2. Create a virtual environment**

```bat
py -m venv .venv
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**4. Configure your environment**

Copy `.env.example` to `.env` and add your Discord bot token:

```dotenv
DISCORD_TOKEN=your_discord_bot_token
BUMP_ROLE_ID=0
```

Enable Message Content Intent in the Discord Developer Portal, and invite the bot with the necessary message permissions and application command scope.

Never commit your real `.env` file.

**5. Run the bot**

```bash
python bot.py
```

## 🔥 DISBOARD Integration

Ringo recognizes successful DISBOARD bump messages and resets a matching reminder's two-hour countdown.

To configure this functionality, create a looping reminder named `DISBOARD Bump`, set its interval to **2 hours**, and select the channel where DISBOARD posts confirmations.

When the countdown expires, Ringo sends a custom embed with `bump_banner.png` and optionally mentions a configured role. It then waits for another successful bump to restart the countdown.

## 📂 Project Structure

```text
Ringo-Bot/
├── bot.py
├── database.py
├── bump_banner.png
├── check_database.py
├── test_reminder.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ How It Works

The bot uses `discord.py` to interact with Discord and runs a scheduled check approximately every 10 seconds.

Reminder configurations and scheduling information are stored in a local SQLite database. Ordinary recurring reminders are rescheduled after delivery, while one-time reminders are deleted.

The bot must stay online to send reminders.

---

**Developed by [HIRGON7](https://github.com/HIRGON7)**

*Built with Python for the Reader's Delight Discord community.*
