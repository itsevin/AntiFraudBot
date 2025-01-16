import ujson as json

async def init_data():
    with open("data/data.json", "w", encoding="utf-8") as f:
        data = {
            "knowledge_push": {
                "group_list": [],
                "friend_list": []
            },
            "example_push": {
                "group_list": [],
                "friend_list": []
            },
            "keyword_detection": {
                "group_list": [],
                "friend_list": []
            },
            "url_detection": {
                "group_list": [],
                "friend_list": []
            }
        }
        json.dump(data, f, ensure_ascii=False, indent=4)
