# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class ChuangYeZuiQianXian(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "https://voice.itjuzi.com/?cat=22&paged=%s"
        self.origin = "桔说社"
        self.label = "创业干货"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not ChuangYeZuiQianXian.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("div", class_="home-wrapper ").findAll("article")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h1").find("a")
                        title = href.get_text()
                        url = href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            ChuangYeZuiQianXian.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img").get("src")
                        rel_date = article.find("time", class_="updated").get("datetime")
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            ChuangYeZuiQianXian.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("JuShuoShe crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("JuShuoShe crawl error. ErrMsg: %s" % str(e))
        finally:
            ChuangYeZuiQianXian.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("article")
        # 删除文章中不必要的不分
        self.extract(article_body.find("header"))
        self.extract(article_body.find("footer"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%dT%H:%M:%S+00:00"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in JuShuoShe. ErrMsg: %s" % str(e))


class ZiBenZheYangKan(ChuangYeZuiQianXian):

    def __init__(self):
        super().__init__()
        self.label = "商业观点"
        self.page_url = "https://voice.itjuzi.com/?cat=5069&paged=%s"


class JuYanYuan(ChuangYeZuiQianXian):

    def __init__(self):
        super().__init__()
        self.label = "经管权威"
        self.page_url = "https://voice.itjuzi.com/?cat=5067&paged=%s"


class ShuJuYouYiSi(ChuangYeZuiQianXian):

    def __init__(self):
        super().__init__()
        self.label = "商业资讯"
        self.page_url = "https://voice.itjuzi.com/?cat=5068&paged=%s"


def crawl():
    items = [ChuangYeZuiQianXian(), ZiBenZheYangKan(), JuYanYuan(), ShuJuYouYiSi()]
    for item in items:
        item.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


