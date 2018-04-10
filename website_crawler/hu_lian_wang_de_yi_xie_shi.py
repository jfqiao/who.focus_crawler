# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import re
import json
import bs4

from website_crawler.crawler import Crawler


class YiXieShiGanHuo(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.origin = "互联网的壹些事"
        self.label = "商业资讯"
        self.page_url = "http://www.yixieshi.com/it/page/%s"

    def crawl(self):
        try:
            page = 1
            while not YiXieShiGanHuo.update_stop:
                resp = requests.get(url=self.page_url % page, headers=YiXieShiGanHuo.headers)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.findAll("div", attrs={"class": re.compile("article-box clearfix excerpt-\d+")})
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h2")
                        title = href.get_text().replace("\n", "")
                        url = href.find("a").get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            YiXieShiGanHuo.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img").get("src")
                        rel_date = article.find("time", class_="item").get_text()
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YiXieShiGanHuo.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date.strftime(Crawler.time_format),
                                                 date.strftime(Crawler.time_format),
                                                 self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("HuLianWangDeYiXieShi crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("HuLianWangDeYiXieShi crawl error. ErrMsg: %s" % str(e))
        finally:
            YiXieShiGanHuo.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, headers=YiXieShiGanHuo.headers)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("article", class_="article-content")
        self.extract_all(article_body.findAll("noscript"))
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
            time_format = "%Y-%m-%d"
            return datetime.datetime.strptime(date_str, time_format)
        except BaseException as e:
            print("HuLianWangDeYiXieShi crawler error in convert time. Time String : %s. ErrMsg: %s" % (date_str, str(e)))

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

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


class YiXieShiDianShang(YiXieShiGanHuo):

    def __init__(self):
        super().__init__()
        self.label = "著名公司"
        self.page_url = "http://www.yixieshi.com/b2b/page/%s"


class YiXieShiYouQu(YiXieShiGanHuo):

    def __init__(self):
        super().__init__()
        self.label = "科技"
        self.page_url = "http://www.yixieshi.com/youqu/page/%s"


class YiXieShiBaoGao(YiXieShiGanHuo):

    def __init__(self):
        super().__init__()
        self.label = "经管权威"
        self.page_url = "http://www.yixieshi.com/report/page/%s"


def crawl():
    gh = YiXieShiGanHuo()
    gh.crawl()
    ds = YiXieShiDianShang()
    ds.crawl()
    yq = YiXieShiYouQu()
    yq.crawl()
    bg = YiXieShiBaoGao()
    bg.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()
