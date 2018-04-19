# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class Explainers(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "https://www.vox.com/explainers"
        self.origin = "Vox"
        self.label = "English"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            resp = requests.get(url=self.page_url)
            if resp.status_code != 200:
                return
            bs_obj = BeautifulSoup(resp.content, "html.parser")
            articles_list = bs_obj.findAll("div", class_="c-compact-river__entry ")
            if len(articles_list) == 0:
                return
            for article in articles_list:
                try:
                    href = article.find("h2").find("a")
                    title = href.get_text()
                    url = href.get("href")
                    select_result = self.select_url(url)
                    if select_result:  # 查看数据库是否已经有该链接
                        Explainers.update_stop = 1  # 如果有则可以直接停止
                        break
                    image_url = article.find("img").get("src")
                    rel_date = article.find("time", class_="c-byline__item").get_text()
                    date = self.convert_date(rel_date)
                    if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                        Explainers.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        break
                    date_str = date.strftime(Crawler.time_format)
                    self.get_article_content(url)
                    self.crawl_image_and_save(image_url)
                    self.write_data_to_sheet(title, url, image_url, date_str,
                                             date_str, self.label, self.origin)
                    self.insert_url(url)
                    print(url)
                except BaseException as e:
                    print("VOX crawl error. ErrMsg: %s" % str(e))
        except BaseException as e:
            print("VOX crawl error. ErrMsg: %s" % str(e))
        finally:
            Explainers.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="article-content")
        # 删除文章中不必要的不分
        self.extract(article_body.find("div", class_="article-footer-ad"))
        self.extract(article_body.find("p", class_="p1"))
        self.extract(article_body.find("iframe"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        """
        发布的时间采用的是英文月份。
        :param date_str:
        :return:
        """
        try:
            if "Today" in date_str:
                date = datetime.datetime.now()
            else:
                date_str = "2018-" + Crawler.replace_white_space(date_str)
                time_format = "%Y-%B%-m"
                date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in VOX. ErrMsg: %s" % str(e))


def crawl():
    cyb = Explainers()
    cyb.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


