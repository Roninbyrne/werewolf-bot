import re
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials (from https://my.telegram.org)
API_ID = 20948356
API_HASH = "6b202043d2b3c4db3f4ebefb06f2df12"

# Bot token from @BotFather
BOT_TOKEN = "8118270568:AAH9fPWU10vGDMIzjhPhs5uwxqgCSLq5KDo"

# MongoDB connection string for storing user data, game state, etc.

MONGO_DB_URI = "mongodb+srv://Combobot:Combobot@combobot.4jbtg.mongodb.net/?retryWrites=true&w=majority&appName=Combobot"

# --------------start.py-------------

# Video or Photo shown on /start (private chat)
START_VIDEO = "https://unitedcamps.in/Images/file_5250.jpg"

HELP_MENU_VIDEO = "https://unitedcamps.in/Images/file_5251.jpg"

HELP_VIDEO_1 = "https://unitedcamps.in/Images/file_5251.jpg"
HELP_VIDEO_2 = "https://unitedcamps.in/Images/file_11452.jpg"
HELP_VIDEO_3 = "https://unitedcamps.in/Images/file_11453.jpg"
HELP_VIDEO_4 = "https://unitedcamps.in/Images/file_11454.jpg"

#------------------------------------

# Log channel ID where bot sends important events/logs (e.g., bans, errors)
LOGGER_ID = -1002059639505

# Video or photo for /stats 
STATS_VIDEO = "https://unitedcamps.in/Images/file_5250.jpg"

# Global ban channel ID where bot sends important gban and ungban info
GBAN_LOGS = -1002059639505

# Owner ID for specific use
OWNER_ID = 7394132959

# Heroku deployment variables (used for updates/restarts)
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# GitHub repo for pulling bot updates
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/Roninbyrne/Elapsed")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("git_token", None)  # Optional GitHub token for private repo access

# Support links
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/PacificArc")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/phoenixXsupport")

# Validate support links
if SUPPORT_CHANNEL:
    if not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHANNEL url is wrong. Please ensure that it starts with https://"
        )

if SUPPORT_CHAT:
    if not re.match(r"(?:http|https)://", SUPPORT_CHAT):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHAT url is wrong. Please ensure that it starts with https://"
        )