'''

1. 拿設定檔去申請圖文選單
2. 把圖片傳給指定選單id
3. 綁定用戶與圖文選單
4. 解除綁定
5. 刪除圖文選單

'''
# 1: richmenu-3415d90ea22067a7a50846f3cd83634a
# 2: richmenu-8a9f7918d4e2c0cf025e44b1d0c95b4a
# 3: richmenu-b84a068b8c77f7fb72c9a942327e8826
from linebot import (LineBotApi)
import json
from linebot.models import RichMenu

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.abspath(os.pardir), '.env'))

# 創造 line_bot_api
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

# 拿設定檔傳給line
# 讀取圖文選單json檔
# 轉成json格式
with open('richmenu_3.json', 'r', encoding='utf8') as json_file:
    rich_menu_json_object=json.load(json_file)
# 將json格式做成Richmenu的變數
richmenu_config=RichMenu.new_from_json_dict(rich_menu_json_object)
# line_bot_api傳給line
rich_menu_id=line_bot_api.create_rich_menu(richmenu_config)
# 把rich_menu打印出來
print(rich_menu_id)


# 把圖片傳給指定的圖文選單id
# 準備圖片, 並載入
# 命令line_bot_api 將圖片上傳到指定圖文選單的id上
with open('richmenu_3.png', 'rb') as image_file:
    response=line_bot_api.set_rich_menu_image(
        rich_menu_id=rich_menu_id,
        content_type='image/png',
        content=image_file
    )
print(response)

# # 綁定用戶與圖文選單
# rich_menu_id='richmenu-3415d90ea22067a7a50846f3cd83634a'
# line_bot_api.link_rich_menu_to_user(
#     user_id='Uddf9fef08390be103dd04930adc57884',
#     rich_menu_id=rich_menu_id
# )


