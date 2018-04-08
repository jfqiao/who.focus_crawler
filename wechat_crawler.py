import requests
import json
from urllib.parse import quote
import bs4
from bs4 import BeautifulSoup
import xlrd
import xlwt
import time
import datetime
import re
import os
import sys


class WechatArticleCrawler(object):

    pattern = "var msg_cdn_url = \"(.*)\";"

    # 获取到图片地址后，文章信息保存的目录。
    write_dir = "/Users/jfqiao/Desktop/write_aritlce_dirs/"

    # 爬取微信文章内容保存的目录,以月份_日期作为文件夹的名称。
    article_dir = "/Users/jfqiao/Desktop/wechat_articles_dir/%s/"

    search_url_format = "http://weixin.sogou.com/weixin?type=2&s_from=input&query=%s"

    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
               "Accept-Encoding": "gzip, deflate",
               "Accept-Language": "en-US,en;q=0.9,zh;q=0.8",
               "Cache-Control": "max-age=0",
               "Connection": "keep-alive",
               "Cookie": "SUID=69E5CD3C2013940A000000005A76803A; SUV=1517715514337126; weixinIndexVisited=1; JSESSIONID=aaabhXqwapxr26XDkJCew; clientId=3909A09A16F96E533C34ABE617396F84; pgv_pvi=571430912; pgv_si=s1131372544; IPLOC=CN1100; SNUID=55B13EA16C6E0ADE62B407146CB10AB2; ABTEST=0|1520310852|v1; sct=8",
               "Host": "weixin.sogou.com",
               "Upgrade-Insecure-Requests": "1",
               "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
               }

    @staticmethod
    def search_by_title(title):
        """
        通过文章的标题在搜狗微信搜索中得到返回结果，爬第一条结果的图片链接。
        :param title:
        :return:
        """
        key_word = quote(title)
        print(WechatArticleCrawler.search_url_format % key_word)
        r = requests.get(WechatArticleCrawler.search_url_format % key_word, headers=WechatArticleCrawler.headers)
        time.sleep(1)
        bs_obj = BeautifulSoup(r.content, "html.parser")
        while bs_obj.find("img", id="seccodeImage") is not None:
            WechatArticleCrawler.headers["Cookie"] = input("输入新的Cookie")
            r = requests.get(WechatArticleCrawler.search_url_format % key_word, headers=WechatArticleCrawler.headers)
            time.sleep(1)
            bs_obj = BeautifulSoup(r.content, "html.parser")
        result_tag = bs_obj.find("ul", class_="news-list")
        if result_tag is None:
            return "", ""
        image_url = result_tag.find("div", class_="img-box").find("img").get("src")
        pos = image_url.find("&url=")
        end_pos = image_url.find("&", pos + 5)
        if end_pos == -1:
            image_url = image_url[pos + 5:]
        else:
            image_url = image_url[pos + 5, end_pos]
        return image_url

    @staticmethod
    def crawl_article_content(url, title):
        res = requests.get(url)   # 爬取文章的内容
        bs_obj = BeautifulSoup(res.content, "html.parser")
        while bs_obj.find("img", id="seccodeImage") is not None:
            WechatArticleCrawler.headers["Cookie"] = input("输入新的Cookie")
            bs_obj = BeautifulSoup(res.content, "html.parser")
        if res.status_code == 404:
            print(url)
            return ""
        js_content = bs_obj.find("div", id="js_content")
        if js_content is None:
            return ""
        # WechatArticleCrawler.save_file(bs_obj.__str__(), title + ".html")  # 保存源代码
        parse_cnt = WechatArticleCrawler.parse_js_content(js_content)    # 获取转化后的形式

        # WechatArticleCrawler.save_file(parse_cnt, url[28:])
        cnt_file_name = url.replace("/", "").replace(":", "")
        WechatArticleCrawler.save_file(parse_cnt, cnt_file_name)
        abstract_cnt = js_content.get_text()[:51].replace("\n", "")   # 获取文章的摘要，并保存摘要
        # WechatArticleCrawler.save_file(abstract_cnt, url[28:] + "_abstract")
        WechatArticleCrawler.save_file(abstract_cnt, cnt_file_name + "_abstract")
        image_url = re.search(WechatArticleCrawler.pattern, bs_obj.__str__()).group(1)
        return image_url

    @staticmethod
    def get_url_and_set(file_path):
        """
        通过已经在西瓜上爬取的文章属性，爬取图片链接以及文章内容。
        :param file_path: 从西瓜上爬取的结果保存所在的文件。
        :return:
        """
        WechatArticleCrawler.mkdir_for_articles()
        read_workbook = xlrd.open_workbook(file_path)
        write_workbook = xlwt.Workbook(encoding="ascii")
        write_sheet = write_workbook.add_sheet("articles")
        read_table = read_workbook.sheet_by_index(0)
        rows_num = read_table.nrows
        for i in range(read_table.ncols):
            write_sheet.write(0, i, label=read_table.cell(0, i).value)
        i = 1
        try:
            while i < rows_num:
                try:
                    title = read_table.cell(i, 0).value
                    url = read_table.cell(i, 1).value
                    # image_url = WechatArticleCrawler.search_by_title(title)
                    image_url = WechatArticleCrawler.crawl_article_content(url, title)
                    if len(image_url) == 0:   # 过滤掉已被发布者删除的文章。
                        i += 1
                        continue
                    write_sheet.write(i, 0, label=title)
                    write_sheet.write(i, 1, label=url)
                    write_sheet.write(i, 2, label=image_url)
                    for j in range(3, read_table.ncols):
                        write_sheet.write(i, j, label=read_table.cell(i, j).value)
                    i = i + 1
                    print(i)
                except BaseException as e:
                    print(e)
        except BaseException as e:
            print(e)
        write_workbook.save(WechatArticleCrawler.write_dir + "result_" + datetime.datetime.now().strftime("%Y-%m-"
                            "%d_%H-%M-%S") + ".xls")

    @staticmethod
    def parse_js_content(bs_obj):
        result = []
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
                if class_list is not None and "__bg_gif" in item.get("class"):  # 去除掉一些背景gif图片
                    continue
                # 图片的宽度小于100不需要
                width = item.get("width")
                try:
                    if width is not None:
                        width = int(width.replace("px", ""))
                        if width < 100:
                            continue
                except ValueError:
                    pass
                # 有的图片是用_width表示的宽度。
                width = item.get("data-w")
                try:
                    if width is not None:
                        width = int(width.replace("px", ""))
                        if width < 50:
                            continue
                except ValueError:
                    pass
                result.append({"type": "image", "data": src})
            elif item.name == "span":
                if WechatArticleCrawler.check_parent(item):
                    result.append({"type": "text", "data": item.__str__()})
        return json.dumps(result)

    @staticmethod
    def check_parent(tag):
        parents = tag.parents
        for item in parents:
            if item is None:
                return 1
            if item.name == "p" or item.name == "span":
                return 0
        return 1

    @staticmethod
    def save_file(content, name):
        f = open(WechatArticleCrawler.article_dir + name, "wt", encoding="utf-8")
        f.write(content.__str__())
        f.close()

    @staticmethod
    def mkdir_for_articles():
        now = datetime.datetime.now()
        date_str = now.strftime("%m_%d-%H_%M")
        WechatArticleCrawler.article_dir = WechatArticleCrawler.article_dir % date_str
        path = WechatArticleCrawler.article_dir
        if not os.path.exists(path):
            cmd = "mkdir %s" % path
            os.system(cmd)


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    WechatArticleCrawler.get_url_and_set("/Users/jfqiao/Desktop/xi_gua_articles/2018-04-08_11-11.xls")
