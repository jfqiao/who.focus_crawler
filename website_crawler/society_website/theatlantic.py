# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class Business(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "https://www.theatlantic.com/business/"
        self.origin = "Theatlantic"
        self.label = "English"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            resp = requests.get(url=self.page_url, headers=Business.headers)
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
                        Business.update_stop = 1  # 如果有则可以直接停止
                        break
                    image_url = article.find("noscript").find("img").get("src")
                    rel_date = article.find("time", class_="c-byline__item").get_text()
                    date = self.convert_date(rel_date)
                    if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                        Business.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        break
                    date_str = date.strftime(Crawler.time_format)
                    self.get_article_content(url)
                    self.crawl_image_and_save(image_url)
                    self.write_data_to_sheet(title, url, image_url, date_str,
                                             date_str, self.label, self.origin)
                    self.insert_url(url)
                    print(url)
                except BaseException as e:
                    print("Theatlantic crawl error. ErrMsg: %s" % str(e))
        except BaseException as e:
            print("Theatlantic crawl error. ErrMsg: %s" % str(e))
        finally:
            Business.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, headers=Business.headers)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="c-entry-content")
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
                time_format = "%Y-%B%d"
                date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in Theatlantic. ErrMsg: %s" % str(e))

    def crawl_image_and_save(self, image_url):
        # 在调用save_file后，调用此方法用于保存图片。
        file_name = image_url.replace(":", "").replace("/", "")
        pos = file_name.find("?")
        if pos > 0:
            file_name = file_name[:pos]
        resp = requests.get(image_url, headers=Business.headers)
        content_type = resp.headers.get("Content-Type")
        f = open(Crawler.write_image_path + "/" + file_name, "wb")
        f.write(resp.content)
        f.close()
        f = open(Crawler.write_image_path + "/" + file_name + ".txt", "wt")
        f.write(content_type)
        f.close()


class Item(Business):

    def __init__(self, category):
        super().__init__()
        self.page_url = "https://www.vox.com/" + category


def crawl():
    categories = ["explainers", "policy-and-politics", "world", "culture", "science-and-health", "identities",
                  "energy-and-environment", "the-big-idea", "technology", "business-and-finance", "first-person"]
    for category in categories:
        item = Item(category)
        item.crawl()


if __name__ == "__main__":
    # Crawler.initialize_workbook()
    crawl()
    # Crawler.save_workbook()


