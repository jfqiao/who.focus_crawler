# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime

from website_crawler.crawler import Crawler


class PinWanCrawlerDuanZi(Crawler):
    """
    品玩爬段子栏目下的文章
    """

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.origin = "品玩"
        self.label = "段子"
        self.page_url = "http://www.pingwest.com/category/duanzi/page/%s/"

    def crawl(self):
        try:
            page = 1
            while not PinWanCrawlerDuanZi.update_stop:
                resp = requests.get(url=self.page_url % page, headers=PinWanCrawlerDuanZi.headers)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.findAll("div", class_="item")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        article_div = article.find("div", class_="news-item")
                        title = article_div.find("h2", class_="title").get_text().replace("\n", "")
                        url = article_div.find("h2", class_="title").find("a").get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            PinWanCrawlerDuanZi.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article_div.find("div", class_="news-thumb").get("style")
                        # 图片标签在style的背景属性中
                        pos_start = image_url.find("(")
                        pos_end = image_url.find(")")
                        image_url = image_url[pos_start + 1: pos_end]
                        rel_date = article.find("span", class_="time").get_text().replace("• ", "")
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            PinWanCrawlerDuanZi.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date.strftime(Crawler.time_format), rel_date,
                                                 self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("PinWan crawl error. ErrMsg: %s" % str(e))
                    # for test crawl one record
                page += 1
        except BaseException as e:
            print("PinWan crawl error. ErrMsg: %s" % str(e))
        finally:
            PinWanCrawlerDuanZi.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, headers=PinWanCrawlerDuanZi.headers)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", id="sc-container")
        # 删除文章中不必要的不分
        self.extract(article_body.find("p", class_="post-footer-wx"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

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
            print("PinWan crawler error in convert time. Time String : %s. ErrMsg: %s" % (date_str, str(e)))

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})


class PinWanRenWu(PinWanCrawlerDuanZi):

    def __init__(self):
        super().__init__()
        self.origin = "品玩"
        self.label = "人物"
        self.page_url = "http://www.pingwest.com/category/figure/page/%s/"


class PinWanTaiDu(PinWanCrawlerDuanZi):

    def __init__(self):
        super().__init__()
        self.origin = "品玩"
        self.label = "态度"
        self.page_url = "http://www.pingwest.com/category/attitude/page/%s/"


class PinWanXinWen(PinWanCrawlerDuanZi):

    def __init__(self):
        super().__init__()
        self.origin = "品玩"
        self.label = "新闻"
        self.page_url = "http://www.pingwest.com/category/news/page/%s/"


class PinWanZhiShi(PinWanCrawlerDuanZi):

    def __init__(self):
        super().__init__()
        self.origin = "品玩"
        self.label = "知识"
        self.page_url = "http://www.pingwest.com/category/knowledge/page/%s/"


class PinWanChanPin(PinWanCrawlerDuanZi):

    def __init__(self):
        super().__init__()
        self.origin = "品玩"
        self.label = "产品"
        self.page_url = "http://www.pingwest.com/category/product/page/%s/"


class PinWanGongSi(PinWanCrawlerDuanZi):

    def __init__(self):
        super().__init__()
        self.origin = "品玩"
        self.label = "公司"
        self.page_url = "http://www.pingwest.com/category/company/page/%s/"


def crawl():
    pw = PinWanCrawlerDuanZi()
    pw.crawl()
    pw = PinWanChanPin()
    pw.crawl()
    pw = PinWanGongSi()
    pw.crawl()
    pw = PinWanRenWu()
    pw.crawl()
    pw = PinWanTaiDu()
    pw.crawl()
    pw = PinWanXinWen()
    pw.crawl()
    pw = PinWanZhiShi()
    pw.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()
