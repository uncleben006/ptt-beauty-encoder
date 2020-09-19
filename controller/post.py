# -*- coding: utf-8 -*
import json
import os
import random

from dotenv import load_dotenv
from linebot.models import TextSendMessage, FlexSendMessage, ImageSendMessage

from helpers.utils import transfer_push_num
from flex_messages.get_comments import get_comments_flex

load_dotenv(os.path.join(os.getcwd(), '.env'))
from linebot import LineBotApi, WebhookHandler
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

# Rick menu config
MAIN_RICH_MENU_ID = os.getenv('RICHMENU_1')
SUB_RICH_MENU_ID_A = os.getenv('RICHMENU_2')
SUB_RICH_MENU_ID_B = os.getenv('RICHMENU_3')


# 回主選單
def return_main(event):
    line_bot_api.link_rich_menu_to_user(
        user_id = event.source.user_id,
        rich_menu_id = MAIN_RICH_MENU_ID
    )

# 下一張圖文選單
def next_menu(event):
    line_bot_api.link_rich_menu_to_user(
        user_id = event.source.user_id,
        rich_menu_id = SUB_RICH_MENU_ID_B
    )

# 上一張圖文選單
def previous_menu(event):
    line_bot_api.link_rich_menu_to_user(
        user_id = event.source.user_id,
        rich_menu_id = SUB_RICH_MENU_ID_A
    )


# 取得推文數: 依照前五篇相似文章平均
def get_push_number(event, user_id, push_num):

    num = 0
    if push_num:
        push_num = json.loads(push_num)
        for push in push_num:
            print(push)
            push = transfer_push_num(push)

            num += int(push)
        num = int(num / len(push_num))
        text = str(num)
    else:
        text = '0'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

# 取得預測留言: 依照前五篇相似文章隨機抽取
def get_comments(event, user_id, comments):

    if comments:
        comments = json.loads(comments)
        text = ''
        result_comment = []

        # 取出所有 po 文的留言
        for comment in comments:
            for i, c in enumerate(comment):
                if c['tag'] not in ['我婆', '戀愛', '女神', '美', '正', '普', '喜歡', '學生', '可以', '醜', '男的', '頭髮', '牙齒', '鼻子',
                                    '門', '推', '誇張', '驚嘆']:
                    comment.pop(i)
            result_comment += comment

        # 打亂並取 10 則留言出來當作留言
        comments_flex_message = get_comments_flex(random.sample(result_comment, 10))
        line_bot_api.reply_message(event.reply_token,
                                   FlexSendMessage(alt_text = '留言預測', contents = comments_flex_message))
    else:
        text = '沒有推文'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

# 取得相似文章: 前三篇
def get_article(event, user_id, slugs):

    if slugs:
        slugs = json.loads(slugs)
        text = ''
        for slug in slugs[:3]:
            text += 'https://www.ptt.cc/bbs/Beauty/' + slug.replace('_', '.') + '.html\n\n'
        text = text[:-2]
    else:
        text = '沒有相似文章'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

# 取得風格標籤: 依照前五篇相似文章的平均分數
def get_tags(event, user_id, comments):

    if comments:
        comments = json.loads(comments)
        text = ''

        result_tags = []
        # 取出所有 po 文的留言
        for comment in comments:
            for i, c in enumerate(comment):
                # 如果風格不符合以下這些標籤，就移除該則留言
                if c['tag'] in ['可愛', '清秀', '年輕', '仙女', '健康', '騷包', '塑膠', '修圖', '素顏', '童顏',
                                '女神', '美', '正', '普', '帥']:
                    print(c['tag'], end = ' ')
                    result_tags.append(c['tag'])

        # 找出所有留言的 tag 並且整理出風格平均
        result_average = {}
        for tag in set(result_tags):
            score = round(result_tags.count(tag) / len(result_tags) * 100, 2)
            result_average[tag] = score
        result_average = sorted(result_average.items(), key = lambda item: item[1], reverse = True)

        for tag, score in result_average:
            text += tag + ': ' + str(score) + '%\n'
        text = text[:-1]
    else:
        text = '無法預測風格'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

# 取得類似圖片: 前三篇相似文章
def get_photos(event, user_id, img_url):

    print(img_url)
    if img_url:
        img_url = json.loads(img_url)
        text = '與下列圖片相似'
        # TODO: 做成 ImageCarousel
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text = text),
                ImageSendMessage(
                    original_content_url = str(img_url[0]),
                    preview_image_url = str(img_url[0])
                ),
                ImageSendMessage(
                    original_content_url = str(img_url[1]),
                    preview_image_url = str(img_url[1])
                ),
                ImageSendMessage(
                    original_content_url = str(img_url[2]),
                    preview_image_url = str(img_url[2])
                )
            ]
        )
    else:
        text = '沒有相似照片'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = text),
        )

# 取得最像明星臉，以及相似程度
def get_star(event, user_id, star_img, star_name, star_distance, star_name_dict):

    if star_img and star_name:
        img_url = os.path.join(os.getenv('BASE_URL'), 'static', 'star_datas', star_name, star_img)
        text = '你的臉與 ' + star_name_dict[star_name] + ' 最像\n\n相似度: ' + str(
            round(((1 - float(star_distance)) * 100), 2)) + '%'
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text = text),
                ImageSendMessage(
                    original_content_url = str(img_url),
                    preview_image_url = str(img_url)
                )
            ]
        )
    else:
        text = "找不到相似的明星"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = text),
        )