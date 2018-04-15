# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import json

from website_crawler.crawler import Crawler


class DoNewsCrawler(Crawler):

    page_url = "http://www.donews.com/ent/more_ent_ajax?page=%s"

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    detail_url = "http://www.donews.com/news/detail/3/%s.html"

    def __init__(self):
        self.origin = "DoNews"

    def crawl(self):
        try:
            page = 1
            while not DoNewsCrawler.update_stop:
                resp = requests.get(url=DoNewsCrawler.page_url % page, headers=DoNewsCrawler.headers)
                if resp.status_code != 200:
                    continue
                # do-news get json result
                articles_list = json.loads(resp.content)
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    title = article.get("title")
                    url = self.detail_url % article.get("source_id")
                    select_result = self.select_url(url)
                    if select_result:  # 查看数据库是否已经有该链接
                        DoNewsCrawler.update_stop = 1  # 如果有则可以直接停止
                        continue
                    image_url = article.get("pic")
                    rel_date = article.get("pubtime")
                    # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                    date = self.convert_date(rel_date)
                    if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                        DoNewsCrawler.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        continue
                    label = article.get("tag")
                    self.get_article_content(url)
                    self.crawl_image_and_save(image_url)
                    self.write_data_to_sheet(title, url, image_url, date.strftime(Crawler.time_format), rel_date,
                                             label, self.origin)
                    self.insert_url(url)
                    print(url)
                page += 1
        except BaseException as e:
            print("DoNews crawl error. ErrMsg: %s" % str(e))

    def get_article_content(self, url):
        resp = requests.get(url, headers=DoNewsCrawler.headers)
        article_html = BeautifulSoup(resp.content, "html.parser")
        article_body = article_html.find("div", class_="article-con")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def convert_date(self, date_str):
        """
        将时间字符串转换为绝对时间，如果已经是绝对时间，则不进行转化。
        传入的字符串的格式基本为：1小时前，1天前，1分钟前，2018-03-20
        :param date_str:
        :return:
        """
        try:
            date_str = self.replace_white_space(date_str)
            if "分" in date_str:
                pos = date_str.find("分")
                mins = int(date_str[:pos])
                time_gap = datetime.timedelta(minutes=mins)
            elif "时" in date_str:
                pos = date_str.find("小")
                hours = int(date_str[:pos])
                time_gap = datetime.timedelta(hours=hours)
            elif "天" in date_str:
                pos = date_str.find("天")
                days = int(date_str[:pos])
                time_gap = datetime.timedelta(days=days)
            else:
                time_gap = None
            if time_gap is not None:
                date = datetime.datetime.now() - time_gap
            else:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d%H:%M:%S")
            return date
        except BaseException as e:
            print("DoNews crawler error in convert time. Time String : %s, ErrMsg: %s" % (date_str, str(e)))


def crawl():
    dn = DoNewsCrawler()
    dn.crawl()
