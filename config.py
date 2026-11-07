import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Картинки лежат прямо рядом с кодом, без подпапок
IMG_DIR = BASE_DIR

# База: по умолчанию рядом с кодом. Если подключишь Persistent Disk на Render,
# задай переменную DB_PATH (например /var/data/game.db)
DB_PATH = os.environ.get("DB_PATH") or os.path.join(BASE_DIR, "game.db")


def _load_env(path):
    env = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


_env = _load_env(os.path.join(BASE_DIR, "setting.env"))


def _get(key, default=""):
    # Переменные Render (Dashboard -> Environment) важнее, чем setting.env
    return os.environ.get(key) or _env.get(key) or default


BOT_TOKEN = _get("BOT_TOKEN") or None
ADMIN_IDS = [int(x.strip()) for x in _get("ADMIN_IDS").split(",") if x.strip().isdigit()]

# Render сам выдаёт PORT для Web Service
PORT = int(_get("PORT", "10000"))
