# -*- coding: utf-8 -*

# $ pip3 install face_recognition or $ git clone git://github.com/ageitgey/face_recognition

import numpy as np
import face_recognition


# 使用用戶臉部向量搜尋 json 檔內最接近的向量，並回傳 標題 圖片網址 slug 推文數 留言內容
def beauty_compare(datas, ens, locs):
    if ens:
        result_datas = []
        for en in ens:
            distances = face_recognition.face_distance(en, datas['vectors'])
            index = distances.argmin()

            result_dict = {}
            result_dict['post_title'] = datas['titles'][index]
            result_dict['img_url'] = datas['imgs'][index]
            result_dict['post_slug'] = datas['slugs'][index]
            result_dict['push_num'] = datas['push'][index]
            result_dict['comments'] = datas['comments'][index]
            result_datas.append(result_dict)

        return result_datas


def star_compare(datas, ens, locs):
    if ens:
        result_datas = []
        print(datas)
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
                datas['titles'].append(data['title'])
                datas['slugs'].append(data['slug'])
                datas['push'].append(data['push'])
                datas['comments'].append(data['comments'])
                datas['imgs'].append(url)
                datas['vectors'].append(vct)

    datas['vectors'] = np.array([np.array(vector) for vector in datas['vectors']])
    return datas


def star_datas_arrage(json_datas):
    datas = {'star_name': [], 'star_img': [], 'vectors': []}
    for data in json_datas:
        if 'face_vector' in data:
            for vct in data['face_vector']:
                datas['star_name'].append(data['name'])
                datas['star_img'].append(data['img'])
                datas['vectors'].append(vct)

    datas['vectors'] = np.array([np.array(vector) for vector in datas['vectors']])
    return datas
