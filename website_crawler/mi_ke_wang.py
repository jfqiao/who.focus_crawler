# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import re

from website_crawler.crawler import Crawler


class YeJieZiXun(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "http://it224.com/category/industry/page/%s"
        self.origin = "米壳网"
        self.label = "商业资讯"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not YeJieZiXun.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    continue
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("div", id="content").findAll("div", attrs={"id": re.compile("post-\d+")})
                if len(articles_list) == 0:
                    break
                for i in range(1, len(articles_list)):
                    try:
                        article = articles_list[i]
                        href = article.find("h2").find("a")
                        title = href.get_text()
                        url = href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            # YeJieZiXun.update_stop = 1  # 如果有则可以直接停止
                            continue
                        image_url = article.find("img").get("src")
                        rel_date = article.find("div", class_="entry-meta").get_text()
                        pos = rel_date.find(" ")
                        pos = rel_date.find(" ", pos + 1)
                        rel_date = Crawler.replace_white_space(rel_date[:pos])
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YeJieZiXun.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("MiKeWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("MiKeWang crawl error. ErrMsg: %s" % str(e))
        finally:
            YeJieZiXun.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="entry-content")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%d"
            if len(date_str) < 8:
                date_str = "2018-" + date_str
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in MiKeWang. ErrMsg: %s" % str(e))


class ShuMaChanPin(YeJieZiXun):

    def __init__(self):
        super().__init__()
        self.page_url = "http://it224.com/category/digital/page/%s"
        self.label = "科技"


class HeiKeJi(YeJieZiXun):

    def __init__(self):
        super().__init__()
        self.page_url = "http://it224.com/category/internet_of_things/page/%s"
        self.label = "科技"


def crawl():
    yjzx = YeJieZiXun()
    yjzx.crawl()
    smcp = ShuMaChanPin()
    smcp.crawl()
    hkj = HeiKeJi()
    hkj.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


