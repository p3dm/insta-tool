# from worker import do_like, do_comment, do_repost, getCommentByAI
# import requests
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# import subprocess
# import json

# Xpath = {
    
#     "search": "",
#     "comment_button": '//*[contains(@content-desc, "Read or add comments")]',
#     "like_button": '//*[@content-desc="Like"]',
#     "send_comment": '//*[@content-desc="Post comment"]',
#     "send_comment_1": '//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]',
#     "search_button": "//*[@resource-id='com.zhiliaoapp.musically:id/j4d' and @content-desc='Search']|//*[@resource-id='com.zhiliaoapp.musically:id/j4d' and @content-desc='Tìm kiếm']",
#     "search_button_2": "//*[@resource-id='com.ss.android.ugc.trill:id/g8v'][2]", 
#     "search_button_3": '//*[@resource-id="com.zhiliaoapp.musically:id/j2p" and @content-desc="Search"]',
#     "search_button_4": '//*[@resource-id="com.ss.android.ugc.trill:id/jb1" and @content-desc="Tìm kiếm"]|//*[@resource-id="com.ss.android.ugc.trill:id/jbh" and @content-desc="Tìm kiếm"]|//*[@resource-id="com.zhiliaoapp.musically:id/jhs"]',
#     "post_1_3": "//*[@resource-id='com.ss.android.ugc.trill:id/s94']",
#     "post_1_1":"//*[@resource-id='com.ss.android.ugc.trill:id/sj7']",
#     "post_1_2":"//*[@resource-id='com.ss.android.ugc.trill:id/n22']",
#     "post_1_4":'//*[@resource-id="com.zhiliaoapp.musically:id/soy"]|//*[@resource-id="com.zhiliaoapp.musically:id/ssj"]',
#     "post_1_5":'//*[@resource-id="com.ss.android.ugc.trill:id/t4i"]|//*[@resource-id="com.ss.android.ugc.trill:id/t2v"]|//*[@resource-id="com.zhiliaoapp.musically:id/txw"]',
#     "share_button": '//*[contains(@content-desc, "Share video")]',
#     "reup_button": '//*[contains(@content-desc,"Add or remove this video from Favorites")]',
#     "profile_button": '//*[@content-desc="Profile"]',
#     "edit_button" : '//*[@text="Edit"]',
#     "update_bio":'//*[@text="Bio"]',
#     "bio_field": "//*[@resource-id='com.ss.android.ugc.trill:id/ekb']|//*[@resource-id='com.zhiliaoapp.musically:id/grs']",
#     "save_button": '//*[@text="Save"]',
#     "close_button": '//*[@content-desc="Close"]',
#     "x_button": "//*[@resource-id='com.ss.android.ugc.trill:id/jvf']",
#     "share_button": '//*[@resource-id="com.ss.android.ugc.trill:id/nwg"]',
#     "share_button_1":'//*[@resource-id="com.zhiliaoapp.musically:id/u2_"]',
#     "repost_button": '//*[@content-desc="Repost"]/android.widget.FrameLayout[1]',
#     "save_button": '//*[contains(@content-desc,"Add or remove this video from Favorites") and @selected="false"]'
# }

# def searchByKeyWord(d, keyword):
#     try:
#         d.xpath(Xpath["search"]).click()



# def flow_1(device, )