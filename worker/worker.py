import sys
import json
import time
import uiautomator2 as u2
import requests
import subprocess
import os
import time
import random
from google.oauth2.service_account import Credentials  # type: ignore[reportMissingImports]
from googleapiclient.discovery import build
from config import load_config

Xpath = {
    "like_button": '//*[@content-desc="Like" and @selected="false"]|//*[@content-desc="Thích" and @selected="false"]',
    "comment_button": '//*[@content-desc="Comment"]',
    "comment_input": '//*[@resource-id="com.instagram.android:id/layout_comment_thread_edittext_multiline"]',
    "comment_submit": '//*[@resource-id="com.instagram.android:id/layout_comment_thread_post_button_icon"]',
    "share_button": '//*[contains(@content-desc, "Share video")]',
    "repost_button": '//*[@content-desc="Repost and @selected="false"]',

}

pkg = "com.instagram.android"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "adb", "windows", "adb.exe"))
SCOPES=["https://www.googleapis.com/auth/spreadsheets"]
_service_cache = None

def _get_service():
    global _service_cache
    if _service_cache is not None:
        return _service_cache

    cfg      = load_config()
    json_path = cfg.get("service_account_path", "")

    if not json_path or not os.path.exists(json_path):
        raise RuntimeError(
            f"Không tìm thấy file service account tại: '{json_path}'\n"
            "Vui lòng upload file JSON trong phần cấu hình."
        )

    creds          = Credentials.from_service_account_file(json_path, scopes=SCOPES)
    _service_cache = build('sheets', 'v4', credentials=creds)
    return _service_cache


def reset_service():
    global _service_cache
    _service_cache = None

def get_bold_phone_rows(spreadsheet_id, sheet_name):
    service = _get_service()
    res = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[sheet_name],
        includeGridData=True
    ).execute()

    rows = res['sheets'][0]['data'][0]['rowData']
    result = []

    for row_index, row in enumerate(rows[1:], start=2):  # bỏ header
        cells = row.get('values', [])
        if len(cells) < 1:
            continue

        phone_cell = cells[0]
        phone_id = phone_cell.get('formattedValue')

        text_fmt = phone_cell.get('userEnteredFormat', {}) \
                              .get('textFormat', {})

        # ❗ chỉ lấy Phone ID được Ctrl+B
        if not text_fmt.get('bold'):
            continue

        def cell(i):
            return cells[i].get('formattedValue') if i < len(cells) else None

        result.append({
            "Phone ID": phone_id,
            "Posting link (drive)": cell(2),
            "caption/hashtag": cell(3),
            "posting time": cell(7),
            "Status": cell(4),
            "Music keyword": cell(5),
            "Running results": cell(6),
            "Avatar": cell(8),
            "Bio": cell(9),
            "Name": cell(10),
            "comment_language": cell(11),
            "Key Word": cell(12),
            "Total Time": cell(13),
            "api_key" : cell(1),
            "schedule":cell(14),
        })

    return result

def get_bold_phone_rows_2(spreadsheet_id, sheet_name):
    service = _get_service()
    res = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[sheet_name],
        includeGridData=True
    ).execute()

    sheet = res["sheets"][0]
    rows = sheet["data"][0].get("rowData", [])

    result = []

    for row_index, row in enumerate(rows[1:], start=2):  # bỏ header
        cells = row.get("values", [])
        if not cells:
            continue

        phone_cell = cells[0]
        phone_id = phone_cell.get("formattedValue")

        text_format = (
            phone_cell  
            .get("userEnteredFormat", {})
            .get("textFormat", {})
        )

        # chỉ lấy Phone ID in đậm (Ctrl+B)
        if not text_format.get("bold"):
            continue

        def cell_value(i):
            if i < len(cells):
                return cells[i].get("formattedValue", "")
            return ""

        result.append({
            "Phone ID": phone_id,
            "view each phone": cell_value(1),
            "schedule": cell_value(3),
            "Comment/ @/ icon (enter)": cell_value(4),
            "seeding language": cell_value(5),
            "niche, topic": cell_value(6),
            "customer portrait": cell_value(7),
            "goalOfInteraction": cell_value(8),
            "interaction orientation": cell_value(9),
            "link": cell_value(10),
            "api_key": cell_value(2)
        })

    return result

def do_like(d):
    if d.xpath(Xpath["like_button"]).exists:
        d.xpath(Xpath["like_button"]).click_exists()

def do_comment(d, comment):
    time.sleep(2)
    d.xpath(Xpath["comment_button"]).click_exists()
    time.sleep(2)
    d.xpath(Xpath["comment_input"]).click_exists()
    time.sleep(3)
    d.send_keys(comment)
    d.xpath(Xpath["comment_submit"]).click_exists()
    time.sleep(2)
    d.press("back")

def do_repost(d):
    d.xpath(Xpath["repost_button"]).click_exists()

def scroll_up(d):
    try:
        d.swipe(500, 1500, 500, 500, duration=0.2)
    except Exception as e:
        return

def scroll_down(d):
    try:
        d.swipe(500, 500, 500, 1500, duration=0.2)
    except Exception as e:
        return


def getCommentByAI(api_key, post_data, seeding_language = None, niche = None, topic = None, customer_portrait = None, goal_of_interaction = None):
    if niche or topic or customer_portrait or goal_of_interaction:       
        prompt = f"""
        Bạn là một AI chuyên tạo comment trên TikTok.  
        Dữ liệu đầu vào:  
        - post_data: {post_data}  
        - seeding_language: {seeding_language}  
        - niche: {niche}  
        - topic: {topic}  
        - customer_portrait: {customer_portrait}  
        - goal_of_interaction: {goal_of_interaction}  

        Yêu cầu:  
        - Sinh ra một comment ngắn gọn, tự nhiên, phù hợp với nội dung post_data.  
        - Comment phải sử dụng đúng seeding_language.  
        - Nội dung phải liên quan đến niche và topic.  
        - Phù hợp với customer_portrait.  
        - Đáp ứng goal_of_interaction.  
        - Chỉ trả về comment, không giải thích gì thêm.
        """
    else:
        prompt = (
            f"Tạo cho tôi bình luận \n"
            f"Lưu ý: comment bằng tiếng {seeding_language} chỉ đưa ra kết quả duy nhất là 1 bình luận từ 5 đến 15 từ, Chỉ trả về kết quả, không giải thích. \n"
            f"không dùng icon\n"
            f"Dựa trên video ngắn trên Tiktok có caption: '{post_data}',\n"
            f"hãy đưa ra một bình luận vui vẻ, tích cực, với góc nhìn khi tôi là người dùng tiktok lướt thấy video có captop này \n"
        )
        


    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash-lite:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 100
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)

    try:
        result = response.json()
    except ValueError:
        raise Exception(f"Gemini API trả về dữ liệu không phải JSON. HTTP {response.status_code}: {response.text}")

    # API có thể trả về error thay vì candidates (ví dụ: invalid key, quota exceeded)
    if "error" in result:
        error_info = result.get("error", {})
        error_message = error_info.get("message", "Unknown Gemini API error")
        error_status = error_info.get("status", "UNKNOWN")
        raise Exception(f"Gemini API error [{error_status}]: {error_message}")

    candidates = result.get("candidates")
    if not candidates:
        raise Exception(f"Gemini API không có candidates. HTTP {response.status_code}. Response: {json.dumps(result, ensure_ascii=False)}")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        raise Exception(f"Gemini API candidates không có parts. Response: {json.dumps(result, ensure_ascii=False)}")

    comment = parts[0].get("text", "").strip()
    if not comment:
        raise Exception(f"Gemini API trả về comment rỗng. Response: {json.dumps(result, ensure_ascii=False)}")

    return comment

def generateKeyWordByAI(comment_language, keyWord, api_key):
    """Generate 5 related keywords and return as list"""
    prompt = (
        f"Tạo cho tôi 5 từ khóa tìm kiếm trên tiktok liên quan đến '{keyWord}' bằng tiếng {comment_language}.\n"
        f"Lưu ý: \n"
        f"- Trả về 5 từ khóa, mỗi từ khóa trên một dòng\n"
        f"- Mỗi từ khóa ngắn gọn từ 1 đến 3 từ khác biệt so với từ ban đầu (unique)\n"
        f"- Chỉ trả về danh sách từ khóa, không đánh số, không giải thích\n"
    )
    URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    res = requests.post(URL, headers=headers, data=json.dumps(payload))

    if res.status_code == 200:
        data = res.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Parse kết quả thành list, loại bỏ dòng rỗng và khoảng trắng thừa
            keywords = [line.strip() for line in text.strip().split('\n') if line.strip()]
            return keywords
        except Exception as e:
            return []
    else:
        return []

def random_sleep(min_seconds, max_seconds):
    """Sleep for a random duration between min_seconds and max_seconds."""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)

def grant_permission(d):
    try:
        if d.xpath('//*[@text="Allow all"]').exists:
            d.xpath('//*[@text="Allow all"]').click_exists()
        if d.xpath('//*[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]').exists:
            d.xpath('//*[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]').click_exists()
        if d.xpath('//*[@resource-id="com.instagram.android:id/igds_headline_headline"]').exists:
            d.xpath('//*[@resource-id="com.instagram.android:id/bb_primary_action_container"]').click_exists()
        if d.xpath('//*[@resource-id="com.instagram.android:id/clips_download_privacy_nux_title"]').exists:
            d.xpath('//*[@resource-id="com.instagram.android:id/clips_download_privacy_nux_button"]').click_exists()
    except Exception as e:
        print(f"Error in grant_permission: {e}")

def update_running_result(spreadsheet_id, sheet_name, phone_id, running_result):
    service = _get_service()

    values_response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name,
    ).execute()

    rows = values_response.get("values", [])
    if not rows:
        raise RuntimeError(f"Sheet '{sheet_name}' không có dữ liệu để cập nhật")

    target_row = None
    phone_id_text = str(phone_id).strip()

    for row_index, row in enumerate(rows[1:], start=2):
        current_phone_id = str(row[0]).strip() if row else ""
        if current_phone_id == phone_id_text:
            target_row = row_index
            break

    if target_row is None:
        raise RuntimeError(
            f"Không tìm thấy Phone ID '{phone_id_text}' trong sheet '{sheet_name}'"
        )

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!G{target_row}",
        valueInputOption="RAW",
        body={"values": [[str(running_result)]]},
    ).execute()

    return target_row

def safe_string(value, default=""):
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in {"", "none", "null"}:
            return default
        return value
    return str(value)