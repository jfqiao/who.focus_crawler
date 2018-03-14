from bs4 import BeautifulSoup
import bs4
import json
import requests


def get_content_from_file(file_path):
    f = open(file_path, "r", encoding="utf-8")
    content = ""
    while 1:
        line = f.readline()
        if len(line) == 0:
            break
        content += line
    f.close()
    return content


def parse_content(content):
    result = []
    bs_obj = BeautifulSoup(content, "html.parser")
    items = bs_obj.descendants
    for item in items:
        if type(item) == bs4.element.NavigableString:
            continue
        # p标签以及对立的span标签都是需要的，但是p标签可能包含span标签
        if item.name == "p":
            if item.find("img") is None:
                # f.write(item.__str__())
                if "请输入标题 " in item.get_text():
                    continue
                result.append({"type": "text", "data": item.__str__()})
        elif item.name == "img":
            src = item.get("data-src")
            if src is None:
                src = item.get("src")
            class_list = item.get("class")
            if class_list is not None and "__bg_gif" in item.get("class"):   # 去除掉一些背景gif图片
                continue
            width = item.get("width")
            try:
                if width is not None:
                    width = int(width.replace("px", ""))
                    if width < 50:
                        continue
            except ValueError:
                pass
            width = item.get("data-w")
            try:
                if width is not None:
                    width = int(width.replace("px", ""))
                    if width < 50:
                        continue
            except ValueError:
                pass
            style_line = item.get("style")

            result.append({"type": "image", "data": src})
        elif item.name == "span":
            if check_parent(item):
                result.append({"type": "text", "data": item.__str__()})
    print(json.dumps(result))


def check_parent(tag):
    parents = tag.parents
    for item in parents:
        if item is None:
            return 1
        if item.name == "p" or item.name == "span":
            return 0
    return 1


if __name__ == "__main__":
    r = requests.get("http://mp.weixin.qq.com/s?__biz=MTY3OTM1NTY2MQ==&mid=2654347022&idx=1&sn=478f6a403c02bdeb7e44c5f0298cd007&scene=0#wechat_redirect")
    parse_content(r.content)
