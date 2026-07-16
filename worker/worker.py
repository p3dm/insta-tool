import sys
import json
import time
import uiautomator2 as u2
import requests
import subprocess
import time
import random
from google.oauth2.service_account import Credentials  # type: ignore[reportMissingImports]
from googleapiclient.discovery import build
from config import load_config

Xpath = {
    "like_button": '//*[@content-desc="Like" and @selected="false"]|//*[@content-desc="Thích" and @selected="false"]',
    "comment_button": '//*[@content-desc="Comment"]',
    "share_button": '//*[contains(@content-desc, "Share video")]',
    "repost_button": '//*[@content-desc="Repost and @selected="false"]',

}

ADB_PATH = r"./adb/windows/adb.exe"
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
            "API_KEY" : cell(1),
            "cron":cell(14),
            "interval":cell(15),
            "date": cell(16)
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
            "cron": cell_value(3),
            "interval"  : cell_value(4),
            "date": cell_value(5),
            "Comment/ @/ icon (enter)": cell_value(6),
            "seeding language": cell_value(7),
            "niche, topic": cell_value(8),
            "customer portrait": cell_value(9),
            "goalOfInteraction": cell_value(10),
            "interaction orientation": cell_value(11),
            "link": cell_value(12),
            "api_key": cell_value(2)
        })

    return result

def do_like(d):
    if d.xpath(Xpath["like_button"]).exists:
        d.xpath(Xpath["like_button"]).click()
def do_comment(d,listComment):
    d.xpath(Xpath["comment_button"]).click()
    time.sleep(2)
    d.xpath('//*[@text="Add comment..."]|//*[@text="Thêm bình luận..."]').click()
    time.sleep(3)
    comments = listComment.split("|")
    random_comment = random.choice(comments)
    d.send_keys(random_comment)
    d.xpath('//*[@content-desc="@2131953937"]|//*[@content-desc="@2131888501"]|//*[@content-desc="@2131888199"]|//*[@content-desc="@2131888218"]|//*[@content-desc="@2131888231"]|//*[@content-desc="Post comment"]|//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]|//*[@content-desc="@2131888282"]|//*[@content-desc="@2131888272"]|//*[@resource-id="com.zhiliaoapp.musically:id/cgt"]').click()
    time.sleep(2)
    w, h = d.window_size()
    x = int(w * 0.5)
    y = int(h * 0.2)
    d.click(x, y)
def do_repost(d):
    d.xpath(Xpath["comment_button"]).click()
# def do_save(d):
#     d.xpath(reupButton_xpath).click_exists(2)

def getCommentByAI(api_key, post_data,seeding_language,niche,topic,customer_portrait,goal_of_interaction):
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