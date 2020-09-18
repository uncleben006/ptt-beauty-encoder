# -*- coding: utf-8 -*

from flask import Flask, request, abort, redirect, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, ImageMessage, PostbackEvent,\
    ImageSendMessage, FlexSendMessage
from json_compare import beauty_compare, get_vector, datas_arrage, star_compare, star_datas_arrage
import json
import os
import random
from dotenv import load_dotenv
import redis
from flex_messages import get_comments
import glob
from flask import render_template
from flask_paginate import Pagination, get_page_parameter

# start app
app = Flask(__name__)
load_dotenv(os.path.join(os.getcwd(), '.env'))

# Line bot config
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# Init Redis
redis_url = os.getenv('REDIS_URL')
r = redis.from_url(redis_url, decode_responses = True, charset = 'UTF-8')

# Rick menu config
MAIN_RICH_MENU_ID = os.getenv('RICHMENU_1')
SUB_RICH_MENU_ID_A = os.getenv('RICHMENU_2')
SUB_RICH_MENU_ID_B = os.getenv('RICHMENU_3')

# Load beauty data
with open(os.path.join(os.getcwd(), 'datas/datas_light.json'), 'r', encoding = "utf-8") as jsonfile:
    beauty_datas = datas_arrage(json.load(jsonfile))

# Load star data
with open(os.path.join(os.getcwd(), 'datas/star_datas.json'), 'r', encoding = "utf-8") as jsonfile:
    star_datas = star_datas_arrage(json.load(jsonfile))

# Load star name
with open(os.path.join(os.getcwd(), 'datas/star_name.json'), 'r', encoding = "utf-8") as jsonfile:
    star_name_dict = json.load(jsonfile)


@app.route("/")
def index():
    return 'Hello'


@app.route("/images")
def images():
    password = request.args.get('password')
    print(password)
    print(os.getenv('PASSWORD'))
    if password != os.getenv('PASSWORD'):
        return redirect(url_for('index'))

    images = glob.glob("static/temp/*")
    page = request.args.get(get_page_parameter(), type = int, default = 1)
    pagination = Pagination(page = page, total = len(images), record_name = 'images', bs_version = 4)
    url = os.getenv('BASE_URL')
    # images = [os.path.join(os.getenv('BASE_URL'), image) for image in images][(page-1)*pagination.per_page:page*pagination.per_page]
    images = images[(page - 1) * pagination.per_page:page * pagination.per_page]
    return render_template('images.html', images = images, pagination = pagination, url = url, page = page,
                           password = password)


@app.route("/delete/static/temp/<img_name>")
def delete(img_name):
    os.remove(os.path.join(os.getcwd(), "static/temp", str(img_name)))
    print('delete', os.path.join(os.getcwd(), "static/temp", str(img_name)))
    images = glob.glob("static/temp/*")
    page = request.args.get(get_page_parameter(), type = int, default = 1)
    password = request.args.get('password')
    return redirect(url_for('images', page = page, password = password))


@app.route("/callback", methods = ['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text = True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    # 取得用戶個資
    user_profile = line_bot_api.get_profile(event.source.user_id)

    line_bot_api.link_rich_menu_to_user(
        user_id = event.source.user_id,
        rich_menu_id = MAIN_RICH_MENU_ID
    )

    # TODO: 把用戶資料存入資料庫
    # 開啟一個檔案, 將用戶個資轉成json 格式, 存入檔案內
    with open("./user.txt", "a") as myfile:
        myfile.write(
            json.dumps(
                vars(user_profile)
            )
        )
        myfile.write('\r\n')
    follow_text_message = TextSendMessage("HI! 歡迎使用~")

    line_bot_api.reply_message(
        event.reply_token, follow_text_message
    )


# TODO: 顯示一些基本資訊，例如給用戶看我們的標籤網站或是請用戶打開圖文選單
# @handler.add(MessageEvent, message = TextMessage)
# def handle_message(event):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text = event.message.text))


@handler.add(MessageEvent, message = ImageMessage)
def handle_image_message(event):
    # reply message
    image_id_text_send_message = TextSendMessage(text = '已經收到圖片')
    line_bot_api.reply_message(event.reply_token, image_id_text_send_message)

    # switch rich menu
    user_id = event.source.user_id
    line_bot_api.link_rich_menu_to_user(
        user_id = user_id,
        rich_menu_id = SUB_RICH_MENU_ID_A
    )

    # save image
    message_id = event.message.id
    content_file = line_bot_api.get_message_content(message_id = message_id)
    img_path = os.path.join(os.getcwd(), 'static/temp/' + message_id + '.jpg')
    with open(img_path, 'wb') as tempfile:
        for chunk in content_file.iter_content():
            tempfile.write(chunk)

    # start predict
    ens, locs = get_vector(img_path)

    # 把配對到的表特資料存入 redis 裡
    beauty_result_datas = beauty_compare(beauty_datas, ens, locs)

    if beauty_result_datas:
        data = beauty_result_datas[0]  # 取第一個配對到的臉
        r.set(user_id + ':push_num', json.dumps(data['push_num'], ensure_ascii = False))
        r.set(user_id + ':comments', json.dumps(data['comments'], ensure_ascii = False))
        r.set(user_id + ':post_slug', json.dumps(data['post_slug'], ensure_ascii = False))
        r.set(user_id + ':post_title', json.dumps(data['post_title'], ensure_ascii = False))
        r.set(user_id + ':img_url', json.dumps(data['img_url'], ensure_ascii = False))

    # 把配對到的明星臉資料存入 redis
    star_result_datas = star_compare(star_datas, ens, locs)

    if star_result_datas:
        data = star_result_datas[0]
        r.set(user_id + ':star_name', data['star_name'])
        r.set(user_id + ':star_img', data['star_img'])
        r.set(user_id + ':star_distance', data['star_distance'])
        print(r.get(user_id + ':star_name'))
        print(r.get(user_id + ':star_img'))
        print(r.get(user_id + ':star_distance'))


@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    postback = event.postback.data
    print(postback)

    if postback == "action=main":
        line_bot_api.link_rich_menu_to_user(
            user_id = event.source.user_id,
            rich_menu_id = MAIN_RICH_MENU_ID
        )

        # delete redis which key prefix is user_id
        for key in r.scan_iter(user_id + ":*"):
            r.delete(key)

    if postback == "action=next":
        line_bot_api.link_rich_menu_to_user(
            user_id = event.source.user_id,
            rich_menu_id = SUB_RICH_MENU_ID_B
        )

    if postback == "action=return":
        line_bot_api.link_rich_menu_to_user(
            user_id = event.source.user_id,
            rich_menu_id = SUB_RICH_MENU_ID_A
        )

    if postback == "action=push_number":
        push_num = r.get(user_id + ':push_num')
        num = 0
        if push_num:
            push_num = json.loads(push_num)
            for push in push_num:
                # print(push)
                if push == '爆':
                    push = 99
                if push == 'XX':
                    push = -99
                num += int(push)
            num = int(num / len(push_num))
            text = str(num)
        else:
            text = '0'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

    if postback == "action=comments":
        comments = r.get(user_id + ':comments')
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
            # random.shuffle(result_comment)
            comments_flex_message = get_comments(random.sample(result_comment, 10))
            # for comment in random.sample(result_comment, 10):
            #     text += comment['status'] + ': ' + comment['content'] + '\n'
            #     print(comment)
            line_bot_api.reply_message(event.reply_token,
                                       FlexSendMessage(alt_text = '留言預測', contents = comments_flex_message))
        else:
            text = '沒有推文'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

    if postback == "action=article":
        slugs = r.get(user_id + ':post_slug')
        if slugs:
            slugs = json.loads(slugs)
            text = ''
            for slug in slugs[:3]:
                text += 'https://www.ptt.cc/bbs/Beauty/' + slug.replace('_', '.') + '.html\n\n'
            text = text[:-2]
        else:
            text = '沒有相似文章'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = text))

    if postback == "action=tags":
        comments = r.get(user_id + ':comments')
        if comments:
            comments = json.loads(comments)
            text = ''

            result_tags = []
            # 取出所有 po 文的留言
            for comment in comments:
                for i, c in enumerate(comment):
                    # 如果風格不符合以下這些標籤，就移除該則留言
                    if c['tag'] in ['可愛', '清秀', '年輕', '仙女', '健康', '騷包', '塑膠', '修圖', '素顏', '童顏']:
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

    if postback == "action=photo":
        img_url = r.get(user_id + ':img_url')
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

    if postback == "action=star":

        star_img = r.get(user_id + ':star_img')
        star_name = r.get(user_id + ':star_name')
        star_distance = r.get(user_id + ':star_distance')
        print(star_img)
        print(star_name)
        print(star_distance)
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


if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 5000)
