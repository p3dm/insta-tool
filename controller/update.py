import random
import time
import subprocess
import os
from urllib.parse import parse_qs, urlparse

import uiautomator2 as u2
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import get_spreadsheet_id, load_config
from worker.worker import (
    ADB_PATH, get_bold_phone_rows, pkg, random_sleep, safe_string,
    update_running_result,
)

Xpath = {
    "profile": '//*[@resource-id="com.instagram.android:id/profile_tab"]',
    "edit_button": '//*[@text="Edit profile"]|//*[@content-desc="Edit profile"]',
    "edit_bio": '//*[@resource-id="com.instagram.android:id/bio"]/android.widget.EditText[1]|//*[@text="Bio"]',
    "edit_name": '//*[@resource-id="com.instagram.android:id/full_name"]/android.widget.EditText[1]|//*[@text="Name"]',
    "bio_field": '//*[@resource-id="com.instagram.android:id/prism_form_field_container"]/android.widget.EditText',
    "name_field": '//*[@resource-id="com.instagram.android:id/prism_form_field_container"]/android.widget.EditText',
    "back_button": '//*[@resource-id="com.instagram.android:id/action_bar_button_back"]',
    "word_count": '//*[@resource-id="com.instagram.android:id/form_field_limit_text"]',
    "save": '//*[@content-desc="Done"]|//*[@resource-id="com.instagram.android:id/action_bar_button_action"]',
    "change_name": '//*[@resource-id="com.instagram.android:id/igds_alert_dialog_primary_button"]|//*[@text="Change name"]',
}

def update_bio(data, sheet_name="seeding_2"):
    device_id = safe_string(data.get("Phone ID"))
    bio = safe_string(data.get("Bio"))
    spreadsheet_id = get_spreadsheet_id()
    if not device_id:
        return
    d = u2.connect(device_id)
    try:
        d.press("home")
        d.app_stop("pkg")
        d.app_clear("com.genfarmer.uiautomator")
        d.app_start(pkg)
        random_sleep(3, 6)
        d.xpath(Xpath["profile"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_bio"]).click()
        random_sleep(2, 4)
        text = d.xpath(Xpath["word_count"]).get_text()
        if text == "0/150":
            d.send_keys(bio)
        else:
            d.xpath(Xpath["bio_field"]).long_click()
            random_sleep(1, 2)
            if d.xpath('//*[@text="Select all"]').exists:
                d.xpath('//*[@text="Select all"]').click()
                d.clear_text()
                random_sleep(3, 6)
                d.send_keys(bio)
            else:
                d.clear_text()
                random_sleep(3, 6)
                d.send_keys(bio)
        random_sleep(3, 6)
        d.xpath(Xpath["save"]).click_exists()
        time.sleep(4)
        if d.xpath(Xpath["back_button"]).exists:
            d.xpath(Xpath["back_button"]).click()
        else:
            d.press("back")
        random_sleep(10, 15)
        d.press("home")
    except Exception as e:
        update_running_result(spreadsheet_id, sheet_name, device_id, f"Lỗi: {e}")


def update_name(data, sheet_name="seeding_2"):
    device_id = safe_string(data.get("Phone ID"))
    name = safe_string(data.get("Name"))
    spreadsheet_id = get_spreadsheet_id()
    if not device_id:
        return
    d = u2.connect(device_id)
    d.press("home")
    d.app_stop(pkg)
    d.app_clear("com.genfarmer.uiautomator")
    try:
        d.app_start(pkg)
        random_sleep(3, 6)
        d.xpath(Xpath["profile"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_name"]).click()
        random_sleep(2, 4)
        text = d.xpath(Xpath["name_field"]).get_text()
        if text.strip() != "" or text == None:
            random_sleep(1, 2)
            d.send_keys(name)
            random_sleep(3, 6)
            d.xpath(Xpath["save"]).click_exists()
            random_sleep(3, 6)
            d.xpath(Xpath["change_name"]).click()
        else:
            d.xpath(Xpath["name_field"]).long_click()
            random_sleep(1, 2)
            if d.xpath('//*[@text="Select all"]').exists:
                d.xpath('//*[@text="Select all"]').click()
                d.clear_text()
                random_sleep(3, 6)
                d.send_keys(name)
            else:
                d.clear_text()
                random_sleep(3, 6)
                d.send_keys(name)
            d.xpath(Xpath["save"]).click_exists()
            random_sleep(3, 6)
            d.xpath(Xpath["change_name"]).click()
        random_sleep(3, 6)
        d.press("back")
        random_sleep(10, 15)
        time.sleep(4)
        d.press("home")
    except Exception as e:
        update_running_result(spreadsheet_id, sheet_name, device_id, f"Lỗi: {e}")


AVATAR_XPATH = {
    "edit_avatar": '//*[@resource-id="com.instagram.android:id/change_avatar_button"]|//*[@text="Edit picture or avatar"]',
    "upload_photo": '//*[@text="Choose from library"]|//*[@content-desc="Choose from library"]|//*[@resource-id="com.instagram.android:id/update_profile_options_list"]/android.widget.Button[1]',
    "next": '//*[@text="Next"]|//*[@content-desc="Next"]',
    "done": '//*[@text="Done"]|//*[@content-desc="Done"]|//*[@text="Finished"]|//*[@resource-id="com.instagram.android:id/next_button_textview"]',
}





# def _drive_file_id(link):
#     """Lấy file ID từ link chia sẻ của đúng một ảnh Google Drive."""
#     parsed = urlparse(safe_string(link))
#     path_parts = [part for part in parsed.path.split("/") if part]
#     if "file" in path_parts and "d" in path_parts:
#         index = path_parts.index("d")
#         if index + 1 < len(path_parts):
#             return path_parts[index + 1]
#     file_id = parse_qs(parsed.query).get("id", [""])[0]
#     if file_id:
#         return file_id
#     raise ValueError("Avatar phải là link Google Drive của một file ảnh")


# def _avatar_download_links(drive_link):
#     """Trả về link tải của chính xác một ảnh được chỉ định trong cột Avatar."""
#     service_account_path = safe_string(load_config().get("service_account_path"))
#     if not service_account_path or not os.path.exists(service_account_path):
#         raise RuntimeError("Không tìm thấy file service account trong cấu hình")
#     credentials = Credentials.from_service_account_file(
#         service_account_path,
#         scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"],
#     )
#     file_id = _drive_file_id(drive_link)
#     file = build("drive", "v3", credentials=credentials).files().get(
#         fileId=file_id,
#         fields="id,name,mimeType,trashed",
#     ).execute()
#     if file.get("trashed") or not file.get("mimeType", "").startswith("image/"):
#         raise ValueError("Link Avatar phải trỏ đến một file ảnh còn tồn tại trên Google Drive")
#     return [f"https://drive.google.com/uc?export=download&id={file['id']}"]


# def distribute_links(phone_ids, download_links):
#     return [
#         {"Phone ID": phone_id, "Link": download_links[index] if index < len(download_links) else None}
#         for index, phone_id in enumerate(phone_ids)
#     ]


def update_avatar(data, sheet_name="seeding"):
    """Download and set the avatar for one Instagram account.

    Link ở cột Avatar phải trỏ đến chính xác một file ảnh Google Drive.
    """
    device_id = safe_string(data.get("Phone ID"))
    spreadsheet_id = get_spreadsheet_id()
    if not device_id:
        raise ValueError("No Phone ID")
    if not spreadsheet_id:
        raise RuntimeError("Lack of spreadsheet_id")

    d = u2.connect(device_id)
    try:
        links = safe_string(data.get("Avatar"))

        # Open the direct link so Chrome saves the image into the device gallery.
        subprocess.run([
                ADB_PATH, "-s", device_id,
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", links + "com.android.chrome"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        d.xpath('//*[@resource-id="com.android.chrome:id/negative_button"]').click_exists(timeout=7)
        random_sleep(3,6)
        if d.xpath('//*[@resource-id="com.android.chrome:id/message"]').exists:
            d.xpath('//*[@resource-id="com.android.chrome:id/message"]').click_exists(timeout=7)
        time.sleep(10)
        d.xpath('//*[@content-desc="Download"]|//*[@text="Tải xuống"]|//*[@scontent-desc="Tải xuống"]|//*[@text="Showing viewer."]/android.view.View[2]/android.view.View[1]/android.view.View[2]/android.view.View[1]/android.widget.Button[1]').click_exists(timeout=15)
        time.sleep(10)
        d.xpath('//*[@text="Download again"]|//*[@text="Tải xuống lần nữa"]|//*[@text="Download"]|//*[@text="Download anyway"]|//*[@text="Tải xuống"]').click_exists(timeout=7)
        d.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]|//*[@text="Download"]').click_exists(timeout=7)
        random_sleep(3,6)
        if d.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').exists:
            d.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').click_exists(timeout=7)
        
        random_sleep(8, 12)
        d.press("home")
        d.app_stop(pkg)
        d.app_start(pkg)
        random_sleep(3, 6)
        d.xpath(Xpath["profile"]).click()
        random_sleep(3, 6)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 6)
        d.xpath(AVATAR_XPATH["edit_avatar"]).click()
        random_sleep(2, 6)
        d.xpath(AVATAR_XPATH["upload_photo"]).click()
        random_sleep(2, 6)
        d.xpath(AVATAR_XPATH["done"]).click()
        if d.xpath(AVATAR_XPATH["next"]).exists:
            d.xpath(AVATAR_XPATH["next"]).click()
        if d.xpath(AVATAR_XPATH["done"]).exists:
            d.xpath(AVATAR_XPATH["done"]).click()
        random_sleep(6, 10)
        d.press("back")
        random_sleep(3, 6)
        update_running_result(spreadsheet_id, sheet_name, device_id, "Done")
    except Exception as exc:
        update_running_result(spreadsheet_id, sheet_name, device_id, f"Error: {exc}")
        raise
    finally:
        d.press("home")
