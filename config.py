# config_manager.py
import os, json, re

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, "user_data")
CONFIG_FILE   = os.path.join(USER_DATA_DIR, "config.json")

os.makedirs(USER_DATA_DIR, exist_ok=True)

_DEFAULTS = {
    "sheet_url":            "",
    "spreadsheet_id":       "",
    "service_account_path": "",
    "running":              False,
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**_DEFAULTS, **json.load(f)}
    return dict(_DEFAULTS)

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def parse_spreadsheet_id(url: str) -> str | None:
    """
    Hỗ trợ cả 2 dạng URL Google Sheet:
      https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0
      https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/
    """
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9\-_]+)', url)
    return match.group(1) if match else None

def get_spreadsheet_id() -> str:
    """Shortcut đọc spreadsheet_id từ config hiện tại."""
    return load_config().get("spreadsheet_id", "")