# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class JiaoWuChu(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    website_url = "http://jwc.cupl.edu.cn"

    def __init__(self):
        self.page_url = "http://jwc.cupl.edu.cn/index/tzgg.htm"
        self.origin = "中国政法大学"
        self.label = ""

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            resp = requests.get(url=self.page_url)
            if resp.status_code != 200:
                return
            bs_obj = BeautifulSoup(resp.content, "html.parser")
            articles_list = bs_obj.find("div", class_="list major").find("ul").findAll("li")
            if len(articles_list) == 0:
                return
            for article in articles_list:
                try:
                    self.label = article.find("a").get_text()[1:-2]
                    href = article.find("a", class_="title")
                    title = href.get_text()
                    url = JiaoWuChu.website_url + href.get("href")[2:]              # url有一个".."回退。
                    select_result = self.select_url(url)
                    if select_result:  # 查看数据库是否已经有该链接
                        JiaoWuChu.update_stop = 1  # 如果有则可以直接停止
                        break
                    image_url = ""                       # 没有图片
                    rel_date = article.find("span").get_text()
                    # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                    date = self.convert_date(rel_date)
                    if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                        JiaoWuChu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        break
                    date_str = date.strftime(Crawler.time_format)
                    self.get_article_content(url)
                    self.crawl_image_and_save(image_url)
                    self.write_data_to_sheet(title, url, image_url, date_str,
                                             date_str, self.label, self.origin)
                    self.insert_url(url)
                    print(url)
                except BaseException as e:
                    print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
        except BaseException as e:
            print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
        finally:
            JiaoWuChu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="content")
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
            print("Convert time error in ZhongGuoZheFaDaXue. ErrMsg: %s" % str(e))


class XinWenDongTai(JiaoWuChu):

    def __init__(self):
        super().__init__()
        self.page_url = "http://jwc.cupl.edu.cn/index/xwdt.htm"


def crawl():
    jwc = JiaoWuChu()
    jwc.crawl()


if __name__ == "__main__":
    # Crawler.initialize_workbook()
    crawl()
    # Crawler.save_workbook()

