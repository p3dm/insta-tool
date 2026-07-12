from google.oauth2.service_account import Credentials
import sys
import json
import time
import uiautomator2 as u2
import subprocess
import time
import random
from worker.worker import getCommentByAI, buff_view, do_like, do_comment, do_repost, do_save

def running_buff_view(data):
    device_id = str(data["Phone ID"])
    device = u2.connect(device_id)
    device.press("home")
    device.app_clear("com.genfarmer.uiautomator")
    view_target = data["view each phone"]
    comments = data["Comment/ @/ icon (enter)"]
    link = data["link"]
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
    if(comments!=""):
        commentInPost = comments
    else:
        try:
            language = data["seeding language"]
            topic = data["niche, topic"]
            customerPortrait = data["customer portrait"]
            goalOfInteractio = data["goalOfInteraction"]
            interactionOrientation = data["interaction orientation"]
            api_key = data["api_key"]
            post_data = device.xpath("//*[@resource-id='com.zhiliaoapp.musically:id/desc']|//*[@resource-id='com.ss.android.ugc.trill:id/desc']").get_text()
            if not api_key:
                commentInPost = None
            else:
                commentInPost = getCommentByAI(api_key, post_data, language, topic, customerPortrait, goalOfInteractio,
                                    interactionOrientation)
        except Exception as e:
            logging.exception("Worker crashed")
    time.sleep(10)
    buff_view(int(view_target.strip()), random.randint(25, 45), device, commentInPost)
    device.press("home")

def buff_view(view_buff,sleep_time,d,listComment):
    special_actions = [
        "comment",
        "like"
    ]
    if listComment == "":
        special_actions.remove("comment")
    actions =  ["view"] * (view_buff - len(special_actions)) + special_actions
    random.shuffle(actions)

    for i in range(1, view_buff + 1):
        try:
            action = actions[i - 1]
            w, h = d.window_size()
            time.sleep(sleep_time)
            d.swipe(w * 0.5, h * 0.88, w * 0.5, h * 0.3, 0.2)
            time.sleep(5)
            d.swipe(w * 0.5, h * 0.3, w * 0.5, h * 0.7, 0.2)
            print(f"{action}")
            if action == "like":
                do_like(d)
            elif action == "comment":
                do_comment(d,listComment)
            # elif action == "repost":
            #     do_repost(d)
            # elif action == "save":
            #     do_save(d)
            else:
                time.sleep(sleep_time)
                continue
            time.sleep(sleep_time)
        except Exception as e:
            continue