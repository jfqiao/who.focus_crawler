# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time
import json

from website_crawler.crawler import Crawler


class XueQiu(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    website_url = "http://xueqiu.com"

    def __init__(self):
        self.page_url = "http://xueqiu.com/v4/statuses/public_timeline_by_category.json?since_id=-1&max_id=%s" \
                        "&count=15&category=-1"
        self.origin = "雪球网"
        self.label = "资讯"
        self.image_url = "https://ss2.baidu.com/6ONYsjip0QIZ8tyhnq/it/u=2622325340,2894838620&fm=58&" \
                         "s=3073C832C4A0D91148EF15D60200C0BA&bpow=121&bpoh=75"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = -1
            hu_xiu_resp = requests.get(XueQiu.website_url, headers=XueQiu.headers)
            cookies_jar = hu_xiu_resp.cookies
            while not XueQiu.update_stop:
                resp = requests.get(url=self.page_url % page, headers=XueQiu.headers, cookies=cookies_jar)
                if resp.status_code != 200:
                    break
                data = json.loads(resp.content)
                articles_list = data.get("list")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        article = json.loads(article.get("data"))
                        url = XueQiu.website_url + article.get("target")
                        title = article.get("title")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            XueQiu.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.get("first_pic")
                        if image_url is None:
                            image_url = self.image_url
                        rel_date = article.get("created_at")
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            XueQiu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("XueQiu crawl error. ErrMsg: %s" % str(e))
                page = data.get("next_max_id")
        except BaseException as e:
            print("XueQiu crawl error. ErrMsg: %s" % str(e))
        finally:
            XueQiu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, headers=XueQiu.headers)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="article__bd__detail")
        # 删除文章中不必要的不分
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            seconds = float(date_str)
            data_time = time.localtime(seconds / 1000)
            date = time.strftime(Crawler.time_format, data_time)
            date = datetime.datetime.strptime(date, Crawler.time_format)
            return date
        except BaseException as e:
            print("Convert time error in XueQiu. ErrMsg: %s" % str(e))


def crawl():
    xq = XueQiu()
    xq.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


