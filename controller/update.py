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
    "first_media": '//android.widget.GridView/*[1]|//androidx.recyclerview.widget.RecyclerView/*[1]',
    "next": '//*[@text="Next"]|//*[@content-desc="Next"]',
    "done": '//*[@text="Done"]|//*[@content-desc="Done"]',
}


def _required_click(d, selector, label):
    element = d.xpath(selector)
    if not element.exists:
        raise RuntimeError(f"Không tìm thấy {label}")
    element.click()
    random_sleep(1, 2)


def _drive_folder_id(link):
    parsed = urlparse(safe_string(link))
    path_parts = [part for part in parsed.path.split("/") if part]
    if "folders" in path_parts:
        index = path_parts.index("folders")
        if index + 1 < len(path_parts):
            return path_parts[index + 1]
    folder_id = parse_qs(parsed.query).get("id", [""])[0]
    if folder_id:
        return folder_id
    raise ValueError("Link folder Avatar không hợp lệ")


def _avatar_download_links(drive_link):
    service_account_path = safe_string(load_config().get("service_account_path"))
    if not service_account_path or not os.path.exists(service_account_path):
        raise RuntimeError("Không tìm thấy file service account trong cấu hình")
    credentials = Credentials.from_service_account_file(
        service_account_path,
        scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"],
    )
    response = build("drive", "v3", credentials=credentials).files().list(
        q=f"'{_drive_folder_id(drive_link)}' in parents and mimeType contains 'image/' and trashed = false",
        pageSize=1000,
        fields="files(id,name)",
        orderBy="name",
    ).execute()
    return [
        f"https://drive.google.com/uc?export=download&id={file['id']}"
        for file in response.get("files", [])
    ]


def distribute_links(phone_ids, download_links):
    return [
        {"Phone ID": phone_id, "Link": download_links[index] if index < len(download_links) else None}
        for index, phone_id in enumerate(phone_ids)
    ]


def update_avatar(data, sheet_name="seeding"):
    """Download and set the avatar for one Instagram account.

    Images in the Drive folder are assigned by position to the bold Phone IDs in
    the same sheet, matching the original intended batch behaviour.
    """
    device_id = safe_string(data.get("Phone ID"))
    spreadsheet_id = get_spreadsheet_id()
    if not device_id:
        raise ValueError("Phone ID rỗng")
    if not spreadsheet_id:
        raise RuntimeError("Thiếu spreadsheet_id trong cấu hình")

    d = u2.connect(device_id)
    try:
        rows = get_bold_phone_rows(spreadsheet_id, sheet_name)
        phone_ids = [safe_string(row.get("Phone ID")) for row in rows if safe_string(row.get("Phone ID"))]
        links = _avatar_download_links(data.get("Avatar"))
        assignments = {item["Phone ID"]: item["Link"] for item in distribute_links(phone_ids, links)}
        image_link = assignments.get(device_id)
        if not image_link:
            raise RuntimeError("Không có ảnh avatar tương ứng với Phone ID này")

        # Open the direct link so Chrome saves the image into the device gallery.
        subprocess.run(
            [ADB_PATH, "-s", device_id, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", image_link],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
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
        _required_click(d, Xpath["profile"], "tab Profile")
        _required_click(d, Xpath["edit_button"], "nút Edit profile")
        _required_click(d, AVATAR_XPATH["edit_avatar"], "nút đổi ảnh đại diện")
        _required_click(d, AVATAR_XPATH["upload_photo"], "tùy chọn chọn ảnh")
        if d.xpath(AVATAR_XPATH["next"]).exists:
            d.xpath(AVATAR_XPATH["next"]).click()
        if d.xpath(AVATAR_XPATH["done"]).exists:
            d.xpath(AVATAR_XPATH["done"]).click()
        random_sleep(3, 6)
        update_running_result(spreadsheet_id, sheet_name, device_id, "Đã xong")
    except Exception as exc:
        update_running_result(spreadsheet_id, sheet_name, device_id, f"Lỗi: {exc}")
        raise
    finally:
        d.press("home")
