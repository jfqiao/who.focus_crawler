# coding=utf-8
import requests
from bs4 import BeautifulSoup
import json
import datetime

from website_crawler.crawler import Crawler


class HuXiuCrawler(Crawler):
    """
    虎嗅网爬最新文章页面. 虎嗅网爬虫方法：通过post方法获取一页数据，收到的数据是json格式。
    """

    post_url = "https://www.huxiu.com/v2_action/article_list"

    update_stop = 0    # stop crawler.

    huxiu_site_url = "https://www.huxiu.com"

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    target_date = datetime.datetime.strptime("", "")

    def __init__(self):
        self.origin = "虎嗅"

    def crawl(self):
        try:
            page = 0                 # 虎嗅网是从第0页开始的。
            while not HuXiuCrawler.update_stop:
                resp = requests.post(url=HuXiuCrawler.post_url, data={"page": page})
                if resp.status_code != 200:
                    continue
                data = json.loads(resp.content).get("data")
                bs_obj = BeautifulSoup(data)
                articles_list = bs_obj.findAll("div", class_="mod-b mod-art")   # class 为 mod-b mod-art的为顶层文章div标签
                for article in articles_list:
                    article_div = article.find("div", class_="mod-thumb ")      # class 为 mod-thumb 标签下有文章的链接,图片链接
                    title = article_div.find("a").get_text().replace("\n", "")  # title should not contains new line
                    url = HuXiuCrawler.huxiu_site_url + article_div.find("a").get_href()  # 相对链接
                    select_result = self.select_url(url)
                    if select_result:                                                      # 查看数据库是否已经有该链接
                        HuXiuCrawler.update_stop = 1                                       # 如果有则可以直接停止
                        continue
                    image_url = article_div.fin("img").get("data-original")             # 图片标签，地址在data-originalsh属性下
                    rel_date = article.find("span", class_="time").get_text()
                    # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                    date = self.convert_date(rel_date)
                    if date < HuXiuCrawler.target_date:    # 比较文章的发表时间，可以保留特定时间段内的文章
                        HuXiuCrawler.update_stop = 1       # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        continue
                    label = article.find("a", class_="column-link").get("text")
                    self.get_article_content(url)
                    self.write_data_to_sheet(title, url, image_url, date.strftime("%Y-%m-%d %H:%M"), rel_date,
                                             label, self.origin)
                    self.insert_url(url)
                page += 1
        except BaseException as e:
            print(e)

    def get_article_content(self, url):
        resp = requests.get(url, headers=HuXiuCrawler.headers)
        article_html = BeautifulSoup(resp.content, "html.parser")
        article_body = article_html.find("div", class_="article-wrap")
        # 删除文章中不必要的不分
        article_body.find("h1", class_="t-h1").extract()
        article_body.find("div", class_="article-author").extract()
        article_body.find("div", class_="neirong-shouquan").extract()
        content = self.parse_content(article_body)
        self.save_file(content, url)

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
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date
        except BaseException as e:
            print("HuXiu crawler error in convert time. Time String : %s" % date_str)