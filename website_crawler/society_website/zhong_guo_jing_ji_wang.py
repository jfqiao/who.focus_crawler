# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class ZhongGuoJingJiWang(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    website_url = "http://www.ce.cn/xwzx/shgj/gdxw"

    def __init__(self):
        self.page_url = "http://www.ce.cn/xwzx/shgj/gdxw/"
        self.origin = "中国经济网"
        self.label = "社会新闻"
        self.image_url = "http://www.ce.cn/img4/celogoh.jpg"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            resp = requests.get(url=self.page_url)
            if resp.status_code != 200:
                return
            bs_obj = BeautifulSoup(resp.content, "html.parser")
            articles_lists = bs_obj.findAll("ul", class_="con")
            if len(articles_lists) == 0:
                return
            for item in articles_lists:
                article_list = item.findAll("li")
                for article in article_list:
                    try:
                        href = article.find("a")
                        title = href.get_text()
                        url = ZhongGuoJingJiWang.website_url + href.get("href")[1:]
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            ZhongGuoJingJiWang.update_stop = 1  # 如果有则可以直接停止
                            continue
                        rel_date = article.find("span", class_="f2").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            ZhongGuoJingJiWang.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            continue
                        date_str = date.strftime(Crawler.time_format)
                        image_url = self.get_article_content(url)
                        if len(image_url) == 0:
                            image_url = self.image_url
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("ZhongGuoJingJiWang crawl error. ErrMsg: %s" % str(e))
        except BaseException as e:
            print("ZhongGuoJingJiWang crawl error. ErrMsg: %s" % str(e))
        finally:
            ZhongGuoJingJiWang.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="TRS_Editor")
        imgs = article_body.findAll("img")
        # 删除文章中不必要的
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)
        if len(imgs) == 0:
            return ""
        else:
            return imgs[0].get("src")

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y%m/%d  %H:%M"
            date = datetime.datetime.strptime("2018" + date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in ZhongGuoJingJiWang. ErrMsg: %s" % str(e))


def crawl():
    cyb = ZhongGuoJingJiWang()
    cyb.crawl()


if __name__ == "__main__":
    crawl()


