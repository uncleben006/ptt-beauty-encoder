def get_comments_flex(comments):
    flex_message = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "留言預測",
                    "color": "#ffff66",
                    "align": "start"
                }
            ],
            "paddingBottom": "10px",
            "paddingTop": "10px",
            "paddingStart": "15px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingBottom": "15px",
            "paddingTop": "10px",
            "contents": []
        },
        "styles": {
            "header": {
                "backgroundColor": "#000088",
                "separator": False
            },
            "hero": {
                "backgroundColor": "#000088"
            },
            "body": {
                "backgroundColor": "#000000"
            }
        }
    }

    for comment in comments:
        print(comment)

        if comment['status'] == '推':
            content = {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "推",
                        "color": "#ffffff",
                        "size": "sm",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": comment['content'],
                        "wrap": True,
                        "color": "#ffff66",
                        "size": "sm",
                        "flex": 10
                    }
                ]
            }

        if comment['status'] == '→':
            content = {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "→",
                        "color": "#ff6666",
                        "size": "sm",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": comment['content'],
                        "wrap": True,
                        "color": "#ffff66",
                        "size": "sm",
                        "flex": 10
                    }
                ]
            }

        if comment['status'] == '噓':
            content = {
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "噓",
                        "color": "#ff6666",
                        "size": "sm",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": comment['content'],
                        "wrap": True,
                        "color": "#ffff66",
                        "size": "sm",
                        "flex": 10
                    }
                ]
            }

        flex_message['body']['contents'].append(content)
    return flex_message
