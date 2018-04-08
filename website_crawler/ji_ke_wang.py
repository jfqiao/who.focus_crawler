# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime

from website_crawler.crawler import Crawler


class JiKeGuanCha(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.page_url = "http://www.fromgeek.com/review/p%s.html"
        self.origin = "极客网"
        self.label = "商业资讯"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not JiKeGuanCha.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    continue
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.findAll("li", class_="textstyle")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h4").find("a")
                        title = href.get("title")
                        url = href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            # JiKeGuanCha.update_stop = 1  # 如果有则可以直接停止
                            continue
                        rel_date = article.find("span", class_="date").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            JiKeGuanCha.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        image_url = self.get_article_content(url)
                        if len(image_url) == 0:
                            continue
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("JiKeWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("JiKeWang crawl error. ErrMsg: %s" % str(e))
        finally:
            JiKeGuanCha.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("article")
        # 删除文章中不必要的
        self.extract(article_body.find("div", class_="correlation"))
        self.extract(article_body.find("div", class_="contribute"))
        imgs = article_body.findAll("img")
        if len(imgs) <= 2:
            return ""
        self.extract(imgs[len(imgs) - 2])
        self.extract(imgs[len(imgs) - 1])
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)
        return imgs[0].get("src")

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%d %H:%M"
            date = datetime.datetime.strptime("2018-" + date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in JiKeWang. ErrMsg: %s" % str(e))


class JiKeYaoWen(JiKeGuanCha):

    def __init__(self):
        super().__init__()
        self.label = "商业新闻"
        self.page_url = "http://www.fromgeek.com/news/p%s.html"


class HangYe(JiKeGuanCha):

    def __init__(self, item):
        super().__init__()
        self.label = "商业资讯"
        self.page_url = ("http://www.fromgeek.com/%s" % item) + "/p%s.html"


def crawl():
    # hy = HangYe("fintech")   # 文章都没有图片
    # hy.crawl()
    jkgc = JiKeGuanCha()
    jkgc.crawl()
    jkyw = JiKeYaoWen()
    jkyw.crawl()
    items = ["blockchain", "retail", "it", "telecom", "ai", "smarthardware", "car", "vc"]
    for item in items:
        hy = HangYe(item)
        hy.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


