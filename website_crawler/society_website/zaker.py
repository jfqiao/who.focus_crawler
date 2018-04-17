# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import bs4
import json

from website_crawler.crawler import Crawler


class Zaker(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "http://www.myzaker.com/channel/14"
        self.origin = "ZAKER"
        self.label = "社会新闻"
        self.image_url = "http://zkres.myzaker.com/static/zaker_web2/img/logo.png?v=20170726"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            first_load = True
            while not Zaker.update_stop:
                resp = requests.get(url=self.page_url, headers=Zaker.headers)
                if resp.status_code != 200:
                    break
                if first_load:
                    bs_obj = BeautifulSoup(resp.content, "html.parser")
                    self.page_url = "http:" + bs_obj.find("input", id="nexturl").get("value")
                    first_load = False
                    articles_list = bs_obj.findAll("div", class_="figure flex-block")
                    if len(articles_list) == 0:
                        break
                    for article in articles_list:
                        try:
                            href = article.find("h2").find("a")
                            title = href.get("title")
                            url = "http:" + href.get("href")
                            select_result = self.select_url(url)
                            if select_result:  # 查看数据库是否已经有该链接
                                break
                            image_url = article.find("a", class_="img").get("style")
                            start = image_url.find("(")
                            end = image_url.find(")")
                            image_url = "http:" + image_url[start + 1: end]
                            rel_date = article.find("div", class_="subtitle").findAll("span")[1].get_text()
                            # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                            date = self.convert_date(rel_date)
                            if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                                Zaker.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                                continue
                            date_str = date.strftime(Crawler.time_format)
                            self.get_article_content(url)
                            self.crawl_image_and_save(image_url)
                            self.write_data_to_sheet(title, url, image_url, date_str,
                                                     date_str, self.label, self.origin)
                            self.insert_url(url)
                            print(url)
                        except BaseException as e:
                            print("Zaker crawl error. ErrMsg: %s" % str(e))
                else:
                    json_obj = json.loads(resp.content)
                    article_list = json_obj.get("data").get("article")
                    self.page_url = "http:" + json_obj.get("data").get("next_url").replace("\\", "")
                    for article in article_list:
                        try:
                            title = article.get("title")
                            url = "http:" + article.get("href").replace("\\", "")
                            select_result = self.select_url(url)
                            if select_result:  # 查看数据库是否已经有该链接
                                break
                            image_url = article.get("img")
                            if len(image_url) == 0:
                                image_url = self.image_url
                            else:
                                image_url = "http:" + image_url.replace("\\", "")
                            rel_date = article.get("marks")[1]
                            # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                            date = self.convert_date(rel_date)
                            if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                                Zaker.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                                continue
                            date_str = date.strftime(Crawler.time_format)
                            self.get_article_content(url)
                            self.crawl_image_and_save(image_url)
                            self.write_data_to_sheet(title, url, image_url, date_str,
                                                     date_str, self.label, self.origin)
                            self.insert_url(url)
                            print(url)
                        except BaseException as e:
                            print("Zaker Crawler error. ErrMsg: %s" % str(e))
        except BaseException as e:
            print("Zaker crawl error. ErrMsg: %s" % str(e))
        finally:
            Zaker.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, headers=Zaker.headers)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="article_content").find("div", id="content")
        # 删除文章中不必要的
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    def parse_content(self, bs_obj):
        result = []
        items = bs_obj.descendants
        for item in items:
            if type(item) == bs4.element.NavigableString:
                continue
            # p标签以及对立的span标签都是需要的，但是p标签可能包含span标签
            if item.name == "p":
                if item.find("img") is None:
                    # f.write(item.__str__())
                    self.insert_line(result, item)
            elif item.name == "img":
                src = item.get("data-original")
                result.append({"type": "image", "data": src})
            elif item.name == "span":
                if self.check_parent(item):
                    self.insert_line(result, item)
                    # result.append({"type": "text", "data": item.__str__()})
        return json.dumps(result).encode("UTF-8").decode("UTF-8")

    @staticmethod
    def convert_date(date_str):
        """
                将时间字符串转换为绝对时间，如果已经是绝对时间，则不进行转化。
                传入的字符串的格式基本为：1小时前，1天前，1分钟前，2018-03-20
                :param date_str:
                :return:
                """
        try:
            if "分" in date_str:
                pos = date_str.find("分")
                mins = int(date_str[:pos])
                time_gap = datetime.timedelta(minutes=mins)
            elif "时" in date_str:
                pos = date_str.find("小")
                hours = int(date_str[:pos])
                time_gap = datetime.timedelta(hours=hours)
            elif "天" in date_str:
                day_gap = 0
                if "昨" in date_str:
                    day_gap = 1
                elif "前" in date_str:
                    day_gap = 2
                time_gap = datetime.timedelta(days=day_gap)
            else:
                time_gap = None
            if time_gap is not None:
                date = datetime.datetime.now() - time_gap
            else:
                date = datetime.datetime.strptime("2018-" + date_str, "%Y-%m-%d")
            return date
        except BaseException as e:
            print("Convert time error in Zaker. ErrMsg: %s" % str(e))


class YuLe(Zaker):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.myzaker.com/channel/9"
        self.label = "娱乐"


class TiYu(Zaker):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.myzaker.com/channel/8"
        self.label = "娱乐"


class HuLianWang(Zaker):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.myzaker.com/channel/5"
        self.label = "资讯"


def crawl():
    yl = YuLe()
    yl.crawl()
    ty = TiYu()
    ty.crawl()
    hlw = HuLianWang()
    hlw.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


