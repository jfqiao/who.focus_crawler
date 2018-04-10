# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time
import json

from website_crawler.crawler import Crawler


class LingShouQianYan(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    article_detail_url = "https://www.pintu360.com/a%s.html"

    def __init__(self):
        self.page_url = "https://www.pintu360.com/service/ajax_article_service.php"
        self.origin = "品途商业评论"
        self.label = "商业资讯"
        self.data = {"fnName": "getArticleList", "type": "classId", "id": "7", "pageNumber": "", "duration": "quarter"}

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 0
            while not LingShouQianYan.update_stop:
                self.data["pageNumber"] = page
                resp = requests.post(self.page_url, data=self.data)
                if resp.status_code != 200:
                    break
                articles_list = json.loads(resp.content)
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        title = article.get("title")
                        url = LingShouQianYan.article_detail_url % article.get("id")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            LingShouQianYan.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.get("imgUrl")
                        rel_date = article.get("onlineTime")
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            LingShouQianYan.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("PinTuWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("PinTuWang crawl error. ErrMsg: %s" % str(e))
        finally:
            LingShouQianYan.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="text")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            seconds = float(date_str) / 1000     # ms
            data_time = time.localtime(seconds)
            date = time.strftime(Crawler.time_format, data_time)
            date = datetime.datetime.strptime(date, Crawler.time_format)
            return date
        except BaseException as e:
            print("Convert time error in PinTuWang. ErrMsg: %s" % str(e))


class ZhiNengKeJi(LingShouQianYan):

    def __init__(self):
        super().__init__()
        self.data["id"] = "10"
        self.label = "科技"


class QuKuaiLian(LingShouQianYan):

    def __init__(self):
        super().__init__()
        self.data["id"] = "87"
        self.label = "商业资讯"


class FanWenYu(LingShouQianYan):

    def __init__(self):
        super().__init__()
        self.data["id"] = "9"
        self.label = "娱乐"


class XinXiaoFei(LingShouQianYan):

    def __init__(self):
        super().__init__()
        self.data["id"] = "8"
        self.label = "商业资讯"


class ChuangYeTouZi(LingShouQianYan):

    def __init__(self):
        super().__init__()
        self.data["id"] = "72"
        self.label = "商业新闻"


def crawl():
    items = [LingShouQianYan(), ZhiNengKeJi(), QuKuaiLian(), FanWenYu(), XinXiaoFei(), ChuangYeTouZi()]
    for item in items:
        item.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


