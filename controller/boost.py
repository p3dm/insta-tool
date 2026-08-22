from google.oauth2.service_account import Credentials
import os
import sys
import json
import logging
import time
import uiautomator2 as u2
import subprocess
import time
import random
from config import get_spreadsheet_id
from worker.worker import getCommentByAI, do_like, do_comment, do_repost, update_running_result, safe_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "adb", "windows", "adb.exe"))



def running_buff_view(data, sheet_name="seeding_2"):
    try:
        commentInPost = ""
        device_id = safe_string(data.get("Phone ID"))
        if not device_id:
            raise ValueError("Phone ID rỗng")
        device = u2.connect(device_id)
        device.press("home")
        device.app_stop("com.genfarmer.uiautomator")
        view_target = safe_string(data.get("view each phone"))
        comments = safe_string(data.get("Comment/ @/ icon (enter)"))
        link = safe_string(data.get("link"))
        spreadsheet_id = get_spreadsheet_id()
        if not link:
            raise ValueError("link rỗng")
        subprocess.run([
                ADB_PATH,
                "-s",
                device_id,
                "shell",
                "am",
                "start",
                "-a",
                "android.intent.action.VIEW",
                "-d",
                link,
                "com.instagram.android",
            ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        time.sleep(10)
        if comments:
            commentInPost = comments
        else:
            try:
                language = safe_string(data.get("seeding language"))
                topic = safe_string(data.get("niche, topic"))
                customerPortrait = safe_string(data.get("customer portrait"))
                goalOfInteractio = safe_string(data.get("goalOfInteraction"))
                interactionOrientation = safe_string(data.get("interaction orientation"))
                api_key = safe_string(data.get("api_key"))
                el = device.xpath("//*[@resource-id='com.instagram.android:id/clips_caption_component']/android.widget.ScrollView[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]")
                post_data = el.attrib.get('content-desc')
                if not api_key:
                    commentInPost = None
                else:
                    commentInPost = getCommentByAI(api_key, post_data, language, topic, customerPortrait, goalOfInteractio,
                                        interactionOrientation)
            except Exception as e:
                print(f"Worker crashed: {e}")
                commentInPost = ""
        time.sleep(10)
        buff_view(int(view_target.strip()), random.randint(25, 45), device, commentInPost)
        device.press("home")
        update_running_result(
            spreadsheet_id,
            sheet_name,
            device_id,
            f"Đã xong"
        )
    except Exception as e:
        update_running_result(
            spreadsheet_id,
            sheet_name,
            device_id,
            f"Lỗi: {e}"
        )

def buff_view(view_buff,sleep_time,d,listComment):
    special_actions = [
        "comment",
        "like"
    ]
    if not listComment or listComment.strip() == "":
        special_actions.remove("comment")
    actions =  ["view"] * (view_buff - len(special_actions)) + special_actions
    random.shuffle(actions)

    for i in range(1, view_buff + 1):
        try:
            action = actions[i - 1]
            w, h = d.window_size()
            d.swipe(w * 0.5, h * 0.88, w * 0.5, h * 0.3, 0.2)
            time.sleep(5)
            d.swipe(w * 0.5, h * 0.3, w * 0.5, h * 0.7, 0.2)
            print(f"{action}")
            if action == "like":
                time.sleep(2)
                do_like(d)
                print("Liked the post")
            elif action == "comment":
                time.sleep(2)
                do_comment(d,listComment)
                print("Commented on the post")
            elif action == "repost":
                time.sleep(2)
                do_repost(d)
                print("Reposted the post")
            # elif action == "save":
            #     do_save(d)
            else:
                time.sleep(sleep_time)
                continue
            time.sleep(sleep_time)
        except Exception as e:
            print("An error occurred while processing the post")
            continue