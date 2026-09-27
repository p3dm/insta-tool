import time
import random
import re
from worker.worker import do_like, do_comment, do_repost, generateKeyWordByAI, getCommentByAI, random_sleep, update_running_result, scroll_up, safe_string
from config import get_spreadsheet_id
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import subprocess
import json
import uiautomator2 as u2


Xpath = {
    "search": '//*[@content-desc="Search and explore"]',
    "reel_button": '//*[@resource-id="com.instagram.android:id/clips_tab"]',
    "comment_button": '//*[contains(@content-desc, "Read or add comments")]',
    "like_button": '//*[@content-desc="Like"]',
    "send_comment": '//*[@content-desc="Post comment"]',
    "send_comment_1": '//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]',
    "search_box": "//*[@resource-id='com.instagram.android:id/action_bar_search_edit_text']",
    "search_profile": '//*[@resource-id="com.instagram.android:id/row_search_profile_image"]',
    "post": '//*[@resource-id="com.instagram.android:id/grid_card_layout_container"][1]',
    "share_button": '//*[contains(@content-desc, "Share video")]',
    "reup_button": '//*[contains(@content-desc,"Add or remove this video from Favorites")]',
    "profile_button": '//*[@content-desc="Profile"]',
    "edit_button" : '//*[@text="Edit"]',
    "update_bio":'//*[@text="Bio"]',
    "bio_field": "//*[@resource-id='com.ss.android.ugc.trill:id/ekb']|//*[@resource-id='com.zhiliaoapp.musically:id/grs']",
    "save_button": '//*[@text="Save"]',
    "close_button": '//*[@content-desc="Close"]',
    "x_button": "//*[@resource-id='com.ss.android.ugc.trill:id/jvf']",
    "repost_button": '//*[@content-desc="Repost"]/android.widget.FrameLayout[1]',
    "save_button": '//*[contains(@content-desc,"Add or remove this video from Favorites") and @selected="false"]'
}

def searchByKeyWord(d, keyWord):
    try:
        d.xpath(Xpath["search"]).click_exists(timeout=7)
        random_sleep(6,15)
        d.xpath(Xpath["search_box"]).click_exists()
        random_sleep(6,15)
        d.send_keys(keyWord)
        random_sleep(6,15)
        d.xpath(Xpath["search_profile"]).click_exists()
        random_sleep(10,20)
        d.xpath(Xpath["post"]).click_exists()
        random_sleep(6,15)
        if d.xpath(Xpath["close_button"]).exists:
            d.xpath(Xpath["close_button"]).click_exists()
            random_sleep(2,3)
    except Exception as e:
        return



def flow1(d, keyWord, comment_language, api_key):
    """Flow 1: Search by keyword and interact"""
    actions = ["comment", "like", "view", "view", "view", "like", "like", "like", "save", "save"]  # Tăng tỷ lệ view và like
    try:
        random_sleep(3, 6)

        # Generate danh sách từ khóa liên quan
        keyword_list = [keyWord]
        if api_key:
            try:
                keyword_list = generateKeyWordByAI(comment_language, keyWord, api_key)
            except Exception:
                keyword_list = [keyWord]
                actions.remove("comment")  # Nếu không có API key, loại bỏ hành động comment
        
        # Search với từng từ khóa trong list
        for current_keyword in keyword_list:
            d.press("home")
            d.app_stop("com.instagram.android")
            d.app_start("com.instagram.android")
            
            random_sleep(10, 12)
            searchByKeyWord(d, current_keyword)
            random_sleep(10, 12)
            
            # Tương tác với 6-10 video
            for i in range(random.randint(10, 30)):
                random_sleep(15, 40)
                chosen_action = random.choice(actions)
                try:
                    if d.xpath(Xpath["x_button"]).exists or d.xpath(Xpath["close_button"]).exists:
                        d.xpath(Xpath["x_button"] + " | " + Xpath["close_button"]).click_exists()
                        scroll_up(d)
                    else:
                        scroll_up(d)
                    if chosen_action == "like":
                        random_sleep(3, 6)
                        do_like(d)
                    if chosen_action == "view":
                        random_sleep(3, 6)
                        pass
                    if chosen_action == "comment":
                        el = d.xpath("//*[@resource-id='com.instagram.android:id/clips_caption_component']/android.widget.scroll_upView[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]")
                        post_data = el.attrib.get('content-desc')
                        comment_text = getCommentByAI(api_key, post_data, comment_language) or "Nice post!"
                        random_sleep(3, 6)
                        do_comment(d, comment_text)
                        d.press("back")
                    if chosen_action == "repost":
                        random_sleep(3, 6)
                        do_repost(d)
                    scroll_up(d)
                except Exception as e:    
                    return                
                random_sleep(10, 12)
                scroll_up(d)
            time.sleep(4)
        time.sleep(10)
        d.press('home')
    except Exception as e:
        print(f"Error: {e}")
    
def flow2(d, comment_language, api_key):
    actions = [ "comment", "like", "view", "view", "view", "view", "like", "like", "like"] 
    try:
        if api_key == None or api_key == "":
           actions.remove("comment")
        else:
            actions = actions
        d.press("home")
        d.app_stop("com.instagram.android")
        d.app_start("com.instagram.android")
        random_sleep(3,5)
        d.xpath(Xpath["reel_button"]).click_exists()
        for i in range(random.randint(10, 30)):
            random_sleep(15, 40)
            chosen_action = random.choice(actions)

            if d.xpath(Xpath["x_button"]).exists or d.xpath(Xpath["close_button"]).exists or not d.xpath(Xpath["comment_button"]).exists or not d.xpath(Xpath["like_button"]).exists:
                d.xpath(Xpath["x_button"] + " | " + Xpath["close_button"]).click_exists()
                scroll_up(d)
            if chosen_action == "like":
                random_sleep(3, 6)
                do_like(d)
            if chosen_action == "view":
                random_sleep(3, 6)
                pass
            if chosen_action == "comment":
                el = d.xpath("//*[@resource-id='com.instagram.android:id/clips_caption_component']/android.widget.scroll_upView[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]")
                post_data = el.attrib.get('content-desc')
                comment_text = getCommentByAI(api_key, post_data, comment_language) or "Nice post!"
                random_sleep(3, 6)
                do_comment(d, comment_text)
                d.press("back")
            if chosen_action == "repost":
                random_sleep(3, 6)
                do_repost(d)
            scroll_up(d)
        time.sleep(10)
        d.press('home')
    except Exception as e:
        print(f"Error: {e}")
        return

def normalize_int(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return None

    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return int(digits)


def main(data, sheet_name = "seeding"):
    device_id = safe_string(data.get("Phone ID"))
    keyWord = safe_string(data.get("Key Word"))
    comment_language = safe_string(data.get("comment_language"))
    api_key = safe_string(data.get("api_key"))
    total_time = normalize_int(data.get("Total Time", ""))
    spreadsheet_id = get_spreadsheet_id()

    if not spreadsheet_id:
        raise RuntimeError("Thiếu spreadsheet_id trong cấu hình")

    d = u2.connect(device_id)
    try:
        if total_time is None:
            while True:
                flow1(d, keyWord, comment_language, api_key)
                flow2(d, comment_language, api_key)
        else:
            start_time = time.time()
            while time.time() - start_time < total_time * 60:
                flow1(d, keyWord, comment_language, api_key)
                flow2(d, comment_language, api_key)
            d.press('home')
            update_running_result(
                spreadsheet_id,
                sheet_name,
                device_id,
                "Done"
            )
    except Exception as e:
        update_running_result(
                spreadsheet_id,
                sheet_name,
                device_id,
                f"Error: {e}"
            )
        