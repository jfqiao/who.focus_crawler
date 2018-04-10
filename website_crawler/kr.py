# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import re
import json

from website_crawler.crawler import Crawler


class DaGongSi(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    detail_url = "http://36kr.com/p/%s.html"

    def __init__(self):
        self.page_url = "http://36kr.com/api/search-column/23?per_page=20&page=%s"
        self.origin = "36氪"
        self.label = "著名公司"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not DaGongSi.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                articles_list = json.loads(resp.content).get("data").get("items")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        title = article.get("title")
                        url = DaGongSi.detail_url % article.get("id")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            DaGongSi.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.get("cover")
                        rel_date = article.get("published_at")
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            DaGongSi.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("36Kr crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("36Kr crawl error. ErrMsg: %s" % str(e))
        finally:
            DaGongSi.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        pattern = re.compile("content\":\"(.*)\",\"cover")
        content_match = re.search(pattern, resp.content.decode("utf-8"))
        article_body = BeautifulSoup(content_match.group(1).replace("\\\"", "\""), "lxml")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%dT%H:%M:%S+08:00"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in 36Kr. ErrMsg: %s" % str(e))


class Item(DaGongSi):

    def __init__(self, label, page_url):
        super().__init__()
        self.label = label
        self.page_url = "http://36kr.com/api/search-column/%s" % page_url + "?per_page=20&page=%s"


def crawl():
    cyb = DaGongSi()
    cyb.crawl()
    items = [["商业资讯", "221"], ["娱乐", "225"], ["科技", "218"], ["商业资讯", "219"], ["商业资讯", "208"], ["创业干货", "103"]]
    for item in items:
        obj = Item(item[0], item[1])
        obj.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


