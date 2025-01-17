# -*- coding: utf-8 -*
import os
import json
import numpy as np
import face_recognition
from dotenv import load_dotenv

# line sdk
load_dotenv(os.path.join(os.getcwd(), '.env'))
from linebot import LineBotApi, WebhookHandler
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

# 用戶傳進來的照片可能會有多張圖，所以 beauty_compare 會回傳陣列，陣列裡面的 dictionary 包含的陣列是前五個最像的文章
# result_datas = [
#     {
#         'post_title': ["正妹..."],
#         'img_url': ["https://imgur...",...],
#         'post_slug': ["M_1592062527_A_038",...],
#         'push_num': [99,32,45,21,99],
#         'comments': [ [ {'status': '推', 'comment_id': 'a3312393', 'content': '日本c是歡樂杯嗎', 'ip': '175.97.4.226', 'comment_time': '02/05 15:45'},... ],[...] ]
#     },
#     {
#         'post_title': [...],
#         'img_url': [...],
#         'post_slug': [...],
#         'push_num': [...],
#         'comments': [...]
#     }
#     ...
# ]
# 使用用戶臉部向量搜尋 json 檔內最接近的向量，並回傳 標題 圖片網址 slug 推文數 留言內容
def beauty_compare(datas, ens, locs):
    if ens:
        result_datas = []
        for en in ens:
            distances = face_recognition.face_distance(en, datas['vectors'])

            # 取得 distances 距離最小前 50 張臉
            # 因距離小的圖片可能重複出現於同一篇文，所以要依照不同的 slugs 選出不同的文章再推送給用戶
            sim_index = distances.argsort()[:50]
            sim_dict = {index: datas['slugs'][index] for index in sim_index}
            temp = []
            sim_post = {}
            for key, val in sim_dict.items():
                if val not in temp:
                    temp.append(val)
                    sim_post[key] = val
            print(sim_post)

            result_dict = {'post_title': [], 'img_url': [], 'post_slug': [], 'push_num': [], 'comments': []}
            for index in list(sim_post.keys())[:5]:
                result_dict['post_title'].append(datas['titles'][index])
                result_dict['img_url'].append(datas['imgs'][index])
                result_dict['post_slug'].append(datas['slugs'][index])
                result_dict['push_num'].append(datas['push'][index])
                result_dict['comments'].append(datas['comments'][index])
            result_datas.append(result_dict)
            # print(result_dict['post_slug'])

        return result_datas


def star_compare(datas, ens, locs):
    if ens:
        result_datas = []
        for en in ens:
            distances = face_recognition.face_distance(en, datas['vectors'])
            index = distances.argmin()

            result_dict = {}
            result_dict['star_name'] = datas['star_name'][index]
            result_dict['star_img'] = datas['star_img'][index]
            result_dict['star_distance'] = distances[index]
            result_datas.append(result_dict)

        return result_datas


# 用意: 先取得用戶上傳圖片的臉部 vector，vector 可以與明星臉共用
def get_vector(img_path):
    img = face_recognition.load_image_file(img_path)
    ens = face_recognition.face_encodings(img)
    locs = face_recognition.face_locations(img)
    return ens, locs


# 用意: 先把資料整理好，存在 background ram ，避免每次載入臉都要跑迴圈降低運算速度
def datas_arrage(json_datas):
    datas = {'titles': [], 'imgs': [], 'slugs': [], 'push': [], 'comments': [], 'vectors': []}
    for data in json_datas:
        if 'face_vector' in data:
            for url, vct in data['face_vector'].items():

                # skip specific post - request by Niels because he think this post have too many negative comments
                if data['slug'] in ['M.1587952919.A.C7B']:
                    print(data['slug'])
                    continue

                datas['titles'].append(data['title'])
                datas['slugs'].append(data['slug'])
                datas['push'].append(data['push'])
                datas['comments'].append(data['comments'])
                datas['imgs'].append(url)
                datas['vectors'].append(vct)

    # 刪除非必要的 tag
    for comments in datas['comments']:
        for index, comment in enumerate(comments):
            if comment['tag'] in ['奶', '腿', '腰', '瘦', '胖', '服裝', '身材', '實用', '女友', '男友', '樓', '道歉', '垃圾', '人名', '雜訊',
                                  '777']:
                # print(index)
                # print(comment['tag'])
                comments.pop(index)

    datas['vectors'] = np.array([np.array(vector) for vector in datas['vectors']])
    return datas


def star_datas_arrage(json_datas):
    datas = {'star_name': [], 'star_img': [], 'vectors': []}
    for data in json_datas:
        if 'face_vector' in data:
            datas['star_name'].append(data['name'])
            datas['star_img'].append(data['img'])
            datas['vectors'].append(data['face_vector'])

    datas['vectors'] = np.array([np.array(vector) for vector in datas['vectors']])
    return datas


def save_image(message_id):
    content_file = line_bot_api.get_message_content(message_id = message_id)
    img_path = os.path.join(os.getcwd(), 'static/temp/' + message_id + '.jpg')
    with open(img_path, 'wb') as tempfile:
        for chunk in content_file.iter_content():
            tempfile.write(chunk)
    return img_path