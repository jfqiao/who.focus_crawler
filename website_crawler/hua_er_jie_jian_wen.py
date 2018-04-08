# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time
import json

from website_crawler.crawler import Crawler


class GongSi(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "https://api-prod.wallstreetcn.com/apiv1/content/articles?category=enterprise&limit=20&" \
                        "cursor=%s"
        self.origin = "华尔街见闻"
        self.label = "公司"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = ""
            while not GongSi.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    continue
                result = json.loads(resp.content, encoding="UTF-8")
                articles_list = result.get("data").get("items")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        if article.get("is_priced"):   # 付费文章，跳过
                            continue
                        title = article.get("title")
                        url = article.get("uri")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            # GongSi.update_stop = 1  # 如果有则可以直接停止
                            continue
                        image_url = article.get("image_uri")
                        rel_date = article.get("display_time")
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            GongSi.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("HuaErJieJianWen crawl error. ErrMsg: %s" % str(e))
                    # for test crawl one record
                page = result.get("data").get("next_cursor")
        except BaseException as e:
            print("HuaErJieJianWen crawl error. ErrMsg: %s" % str(e))
        finally:
            GongSi.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, headers=GongSi.headers)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="node-article-content")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            seconds = float(date_str)
            data_time = time.localtime(seconds)
            date = time.strftime(Crawler.time_format, data_time)
            date = datetime.datetime.strptime(date, Crawler.time_format)
            return date
        except BaseException as e:
            print("Convert time error in HuaErJieJianWen. ErrMsg: %s" % str(e))


class JingJi(GongSi):

    def __init__(self):
        super().__init__()
        self.label = "财经新闻"
        self.page_url = "https://api-prod.wallstreetcn.com/apiv1/content/articles?category=ecomomy&limit=20&cursor=%s"


class ShuJu(GongSi):

    def __init__(self):
        super().__init__()
        self.label = "商业新闻"
        self.page_url = "https://api-prod.wallstreetcn.com/apiv1/content/articles?category=charts&limit=20&cursor=%s"


def crawl():
    gs = GongSi()
    gs.crawl()
    jj = JingJi()
    jj.crawl()
    sj = ShuJu()
    sj.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


