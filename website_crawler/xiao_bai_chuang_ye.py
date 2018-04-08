# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class XiaoBaiChuangYe(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "https://www.ponote.com/page/%s"
        self.origin = "创业邦"
        self.label = ""

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not XiaoBaiChuangYe.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    continue
                bs_obj = BeautifulSoup(resp.content, "lxml")
                articles_list = bs_obj.find("div", class_="content").findAll("article")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h2").find("a")
                        title = href.get_text()
                        url = href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            # XiaoBaiChuangYe.update_stop = 1  # 如果有则可以直接停止
                            continue
                        image_url = article.find("img")
                        if image_url is None:
                            continue
                        image_url = image_url.get("data-original")
                        rel_date = article.find("p", class_="text-muted time").get_text()
                        pos = rel_date.rfind(" ")
                        rel_date = rel_date[pos + 1:]
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            XiaoBaiChuangYe.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("XiaoBaiChuangYe crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("XiaoBaiChuangYe crawl error. ErrMsg: %s" % str(e))
        finally:
            XiaoBaiChuangYe.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("article")
        # 删除文章中不必要的
        self.extract_all(article_body.findAll("div"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%d"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in XiaoBaiChuangYe. ErrMsg: %s" % str(e))


def crawl():
    xbcy = XiaoBaiChuangYe()
    xbcy.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


