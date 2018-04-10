# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class KeJiLie(Crawler):

    """
        图片有防盗链，无法直接在小程序中加载
    """

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36",
               "Referer": "http://www.kejilie.com"}

    def __init__(self):
        self.page_url = "http://www.kejilie.com/toindex.do?currentPage=%s#news"
        self.origin = "科技猎"
        self.label = "商业资讯"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not KeJiLie.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.findAll("li", class_="am-g am-list-item-desced am_list_li")
                if len(articles_list) == 0:
                    break
                for i in range(2, len(articles_list)):
                    try:
                        article = articles_list[i]
                        href = article.find("h3").find("a")
                        title = href.get_text()
                        url = href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            KeJiLie.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img")
                        if image_url is None:
                            continue
                        image_url = image_url.get("src")
                        rel_date = article.find("span", class_="am_news_time").find("time").get("title")
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            KeJiLie.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("KeJiLie crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("KeJiLie crawl error. ErrMsg: %s" % str(e))
        finally:
            KeJiLie.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="so-content")
        self.extract(article_body.find("div", class_="ggyd"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%d %H:%M:%S"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in KeJiLie. ErrMsg: %s" % str(e))

    def crawl_image_and_save(self, image_url):
        # 在调用save_file后，调用此方法用于保存图片。
        file_name = image_url.replace(":", "").replace("/", "")
        pos = file_name.find("?")
        if pos > 0:
            file_name = file_name[:pos]
        resp = requests.get(image_url, headers=self.headers)
        f = open(Crawler.image_dir + "/" + file_name, "wb")
        f.write(resp.content)
        f.close()


def crawl():
    kjl = KeJiLie()
    kjl.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()
