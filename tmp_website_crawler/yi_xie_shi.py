
# coding=utf-8
import requests
from bs4 import BeautifulSoup
import bs4
import datetime
import re
import json

from website_crawler.crawler import Crawler


class YiXieShiCrawler(Crawler):
    """
    品玩爬段子栏目下的文章
    """

    page_url = "http://www.yixieshi.com/youqu/page/%s"

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.origin = "互联网的壹些事"

    def crawl(self):
        try:
            page = 1
            while not YiXieShiCrawler.update_stop:
                resp = requests.get(url=YiXieShiCrawler.page_url % page, headers=YiXieShiCrawler.headers)
                if resp.status_code != 200:
                    continue
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("div", class_="row").findAll("div", attrs={"class": re.compile("article-box clearfix excerpt-\d*")})  # 顶层文章div标签
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    title = article.find("h2").get_text().replace("\n", "")  # title should not contains new line
                    url = article.find("h2").find("a").get("href")  # 相对链接
                    select_result = self.select_url(url)
                    if select_result:  # 查看数据库是否已经有该链接
                        YiXieShiCrawler.update_stop = 1  # 如果有则可以直接停止
                        break
                    image_url = article.find("div", class_="thumbnail").find("img").get("src")   # 图片标签
                    rel_date = article.find("time", class_="item").get_text()
                    # 文章发布的时间，yyyy-mm-dd
                    date = self.convert_date(rel_date)
                    if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                        YiXieShiCrawler.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        break
                    label = "有趣"
                    self.get_article_content(url)
                    self.crawl_image_and_save(image_url)
                    self.write_data_to_sheet(title, url, image_url, date.strftime(Crawler.time_format), rel_date,
                                             label, self.origin)
                    self.insert_url(url)
                    print(url)
                page += 1
        except BaseException as e:
            print("YiXieShi crawl error. ErrMsg: %s" % str(e))

    def get_article_content(self, url):
        try:
            resp = requests.get(url, headers=YiXieShiCrawler.headers)
            article_html = BeautifulSoup(resp.content, "lxml")
            article_body = article_html.find("div", class_="post-con clearfix")
            # 删除文章中不必要的不分
            self.extract(article_body.find("div", class_="article-meta"))
            self.extract(article_body.find("div", class_="post-tag"))
            self.extract(article_body.find("div", class_="reshare clearfix center-block"))
            self.extract(article_body.find("div", attrs={"id": re.compile("BAIDU_SSP.*")}))
            self.extract_all(article_body.findAll("noscript"))
            content = self.parse_content(article_body)
            self.save_file(content, url)
            self.save_abstract(article_body, url)
        except BaseException as e:
            print("Get article content error. URL: %s ErrMsg: %s" % (url, str(e)))
            raise BaseException()

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
            print("YiXieShi crawler error in convert time. Time String : %s, ErrMsg: %s" % (date_str, e))

    def parse_content(self, bs_obj):
        result = []
        items = bs_obj.descendants
        for item in items:
            if type(item) == bs4.element.NavigableString:
                continue
            # p标签以及对立的span标签都是需要的，但是p标签可能包含span标签
            if item.name == "p":
                if item.find("img") is None:
                    self.insert_line(result, item)
            elif item.name == "img":
                src = item.get("data-lazy-src")
                if src is None or len(src) == 0:
                    src = item.get("src")
                width = item.get("width")
                try:
                    if width is not None:
                        width = int(width.replace("px", ""))
                        if width < 50:
                            continue
                except ValueError:
                    pass
                width = item.get("data-w")
                try:
                    if width is not None:
                        width = int(width.replace("px", ""))
                        if width < 50:
                            continue
                except ValueError:
                    pass
                result.append({"type": "image", "data": src})
            elif item.name == "span":
                if self.check_parent(item):
                    self.insert_line(result, item)
                    # result.append({"type": "text", "data": item.__str__()})
        return json.dumps(result).encode("UTF-8").decode("UTF-8")

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})


def crawl():
    yxs = YiXieShiCrawler()
    yxs.crawl()
