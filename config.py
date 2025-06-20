import os
from os import environ

class Config:
    # Bot Configuration
    API_ID_ENV = environ.get("API_ID", "28614709")
    API_HASH_ENV = environ.get("API_HASH", "f36fd2ee6e3d3a17c4d244ff6dc1bac8")

    if API_ID_ENV.isdigit():
        API_ID = int(API_ID_ENV)
        API_HASH = API_HASH_ENV
    elif API_HASH_ENV.isdigit():
        API_ID = int(API_HASH_ENV)
        API_HASH = API_ID_ENV
    else:
        API_ID = 0
        API_HASH = ""

    BOT_TOKEN = environ.get("BOT_TOKEN", "7921283663:AAHlHXQHMa0LAnbyFI-9yquzNDV_aZLoDaM")
    BOT_USERNAME = environ.get("BOT_USERNAME", "AutoRenameDBot")

    # Admin Configuration
    try:
        ADMIN = list(map(int, environ.get("ADMIN", "1077880102").split()))
    except ValueError:
        ADMIN = []
        print("Warning: ADMIN environment variable is not a valid list of integers.")
    ADMINS = ADMIN  # For compatibility

    # ✅ Fix begins: move DB vars inside class
    DB_URL = environ.get("DB_URL", "mongodb+srv://newleech:newleech@cluster0.9islxvy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME = environ.get("DB_NAME", "AutoRenameBot")

    # Channels Configuration
    FORCE_SUB_CHANNELS = environ.get("FORCE_SUB_CHANNELS", "-1001533796760").split(",") if environ.get("FORCE_SUB_CHANNELS") else []
    LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1002578247466")) if environ.get("LOG_CHANNEL") else None

    # Media Configuration
    PORT = int(environ.get("PORT", "8080"))
    START_PIC = environ.get("START_PIC", "https://i.ibb.co/M5fHdYxt/9aa5e0bdcc9c.jpg")
    SETTINGS_PHOTO = environ.get("SETTINGS_PHOTO", "https://i.ibb.co/M5fHdYxt/9aa5e0bdcc9c.jpg")

    # Server Configuration
    WEBHOOK = environ.get("WEBHOOK", "True").lower() == "true"
    BOT_UPTIME = environ.get("BOT_UPTIME", "")

    # Token System Configuration
    TOKEN_ID_LENGTH = 8
    SHORTENER_API = environ.get("SHORTENER_API", "72ac8c94409d87e12b5357265192b637769ae67f")
    SHORTENER_URL = environ.get("SHORTENER_URL", "urlshortx.com")

    # File Processing Configuration
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    DOWNLOAD_LOCATION = "./downloads/"

    # Anti-NSFW Configuration
    ANTI_NSFW_ENABLED = environ.get("ANTI_NSFW_ENABLED", "True").lower() == "true"
