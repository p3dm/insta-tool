import logging
import uiautomator2 as u2
import sys
import os
import json
import time
import uiautomator2 as u2
import subprocess
import time
import random
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import load_config, get_spreadsheet_id
from worker.worker import getCommentByAI, do_like, do_comment, do_repost, random_sleep, update_running_result

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "adb", "windows", "adb.exe"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(BASE_DIR), "posting-debug.log"), encoding="utf-8")
    ]
)

Xpath = {
    "create_button": '//*[@resource-id="com.instagram.android:id/action_bar_buttons_container_left"]',
    "reel_button": '//*[@text="REEL"]',
    "video": '//android.widget.GridView/android.view.ViewGroup[1]',
    "text_field": '//*[@resource-id="com.instagram.android:id/caption_input_text_view"]',
    "audio_button": '//*[@resource-id="com.instagram.android:id/clips_action_bar_add_music_button"]',
    "audio": '//*[@resource-id="com.instagram.android:id/track_container" and @index = "0"]',
    "profile_tab": '//*[@resource-id="com.instagram.android:id/profile_tab"]'
    
}


def reset_service():
    global _service_cache
    _service_cache = None

def running_post_video(data, sheet_name="seeding"):
    device_id = str(data["Phone ID"])
    link = data["Posting link (drive)"]
    caption = str(data["caption/hashtag"])
    music = data["Music keyword"]
    spreadsheet_id = get_spreadsheet_id()

    if not spreadsheet_id:
        raise RuntimeError("Thiếu spreadsheet_id trong cấu hình")

    device = u2.connect(device_id)
    device.press("home")
    device.app_stop("com.instagram.android")
    device.app_clear("com.genfarmer.uiautomator")
    time.sleep(2)
    subprocess.run([
        ADB_PATH, "-s", device_id,
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", link + "com.android.chrome"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW
    )
    device.xpath('//*[@resource-id="com.android.chrome:id/negative_button"]').click_exists(timeout=7)
    random_sleep(3,6)
    if device.xpath('//*[@resource-id="com.android.chrome:id/message"]').exists:
        device.xpath('//*[@resource-id="com.android.chrome:id/message"]').click_exists(timeout=7)
    time.sleep(10)
    device.xpath('//*[@content-desc="Download"]|//*[@text="Tải xuống"]|//*[@scontent-desc="Tải xuống"]|//*[@text="Showing viewer."]/android.view.View[2]/android.view.View[1]/android.view.View[2]/android.view.View[1]/android.widget.Button[1]').click_exists(timeout=15)
    time.sleep(10)
    device.xpath('//*[@text="Download again"]|//*[@text="Tải xuống lần nữa"]|//*[@text="Download"]|//*[@text="Download anyway"]|//*[@text="Tải xuống"]').click_exists(timeout=7)
    device.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]|//*[@text="Download"]').click_exists(timeout=7)
    random_sleep(3,6)
    if device.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').exists:
        device.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').click_exists(timeout=7)

    time.sleep(60)
    
    try:
        upload_video(device,music,caption)
        logging.info("Posting finished successfully for device=%s", device_id)
        update_running_result(
            spreadsheet_id,
            sheet_name,
            device_id,
            "Đã xong"
        )
    except Exception as exc:
        logging.exception("Posting worker crashed for device=%s", device_id)
        update_running_result(
            spreadsheet_id,
            sheet_name,
            device_id,
            f"Lỗi: {exc}"
        )
        raise

def upload_video(d, music, caption):
    logging.info("Starting Instagram upload flow")
    d.press("home")
    d.app_stop("com.instagram.android")
    d.app_start("com.instagram.android")
    random_sleep(3, 5)
    d.xpath('//*[@resource-id="com.instagram.android:id/feed_tab"]').click_exists()
    random_sleep(5, 10)
    d.xpath(Xpath["create_button"]).click_exists()

    random_sleep(5, 10)
    d.xpath('//*[@text="Next"]').click_exists()
    random_sleep(5, 10)
    random_sleep(3,4)
    if music:
        d.xpath(Xpath["audio_button"]).click_exists()
        random_sleep(5, 10)
        d.xpath('//*[@resource-id="com.instagram.android:id/row_search_edit_text"]').click_exists()
        random_sleep(3,5)
        d.send_keys(music)
        random_sleep(3,5)
        d.xpath('//*[@resource-id="com.instagram.android:id/select_button_tap_target"]').click_exists()
        random_sleep(3,5)
        d.xpath('//*[@content-desc="Done"]').click_exists()

    d.xpath('//*[@text="Next"]').click_exists()
    random_sleep(5, 10)
    if caption != None or caption.strip() != "":
        d.xpath(Xpath["text_field"]).click_exists()
        random_sleep(3,5)
        d.send_keys(caption)
    random_sleep(3,5)
    d.xpath('//*[@content-desc="Next"]').click_exists()
    random_sleep(3,6)
    d.xpath('//*[@text="Share"]').click_exists()
    random_sleep(3,6)
    d.xpath(Xpath['profile_tab']).click()
    random_sleep(7,17)
    d.press("home")
    logging.info("Upload flow completed")

