# -*- coding: utf-8 -*

import os
import json
import glob
import redis
from dotenv import load_dotenv

# flask
from flask import Flask, request, abort, redirect, url_for
from flask import render_template
from flask_paginate import Pagination, get_page_parameter

# line sdk
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage, \
    FollowEvent, ImageMessage, PostbackEvent

# custom module
from controller.post import return_main, previous_menu, next_menu, get_push_number, get_comments, get_article, get_tags,\
    get_photos, get_star
from controller.image import beauty_compare, get_vector, datas_arrage, star_compare, star_datas_arrage, save_image

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
with open(os.path.join(os.getcwd(), 'datas/datas_final.json'), 'r', encoding = "utf-8") as jsonfile:
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
    if request.args.get('password'):
        if request.args.get('password') == os.getenv('PASSWORD'):
            password = request.args.get('password')
        else:
            password = None
    else:
        password = None

    images = glob.glob("static/temp/*")
    page = request.args.get(get_page_parameter(), type = int, default = 1)
    pagination = Pagination(page = page, total = len(images), record_name = 'images', bs_version = 4)
    url = os.getenv('BASE_URL')

    # 依照時間排序
    images_dict = {image: os.path.getmtime(image) for image in images}
    images_dict = {k: v for k, v in sorted(images_dict.items(), key = lambda item: item[1])}
    images = list(images_dict.keys())

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
    with open("./user.json", "a") as user_file:
        user_file.write(
            json.dumps(
                vars(user_profile)
            )
        )
        user_file.write('\r\n')
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
    img_path = save_image(message_id)

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


@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    postback = event.postback.data
    print(postback)

    if postback == "action=main":
        return_main(event)
        # delete redis which key prefix is user_id
        for key in r.scan_iter(user_id + ":*"):
            r.delete(key)

    if postback == "action=next":
        next_menu(event)

    if postback == "action=return":
        previous_menu(event)

    if postback == "action=push_number":
        push_num = r.get(user_id + ':push_num')
        get_push_number(event, user_id, push_num)

    if postback == "action=comments":
        comments = r.get(user_id + ':comments')
        get_comments(event, user_id, comments)

    if postback == "action=article":
        slugs = r.get(user_id + ':post_slug')
        get_article(event, user_id, slugs)

    if postback == "action=tags":
        comments = r.get(user_id + ':comments')
        get_tags(event, user_id, comments)

    if postback == "action=photo":
        post_title = r.get(user_id + ':post_title')
        img_url = r.get(user_id + ':img_url')
        get_photos(event, user_id, img_url, post_title)

    if postback == "action=star":
        star_img = r.get(user_id + ':star_img')
        star_name = r.get(user_id + ':star_name')
        star_distance = r.get(user_id + ':star_distance')
        get_star(event, user_id, star_img, star_name, star_distance, star_name_dict)


if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 5000)
