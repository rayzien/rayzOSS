# rayzOSS Configuration Manager
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import os
import json
import subprocess

CONFIG_DIR = os.path.expanduser("~/.rayzoss")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def init_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"token": "", "shards": []}, f, indent=4)

def load_config():
    init_config()
    try:
        with open(CONFIG_FILE, 'r') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {"token": "", "shards": []}

    # Auto-detect token if not explicitly stored
    if not cfg.get("token"):
        # 1. Check environment variables
        env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if env_token:
            cfg["token"] = env_token.strip()
        else:
            # 2. Check GitHub CLI credentials
            try:
                res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0 and res.stdout.strip():
                    cfg["token"] = res.stdout.strip()
            except Exception:
                pass
    return cfg

def save_config(config):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
