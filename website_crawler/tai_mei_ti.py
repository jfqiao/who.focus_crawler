# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime

from website_crawler.crawler import Crawler


class DaGongSi(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    site_url = "http://www.tmtpost.com"

    def __init__(self):
        self.page_url = "http://www.tmtpost.com/column/2446153/%s"
        self.origin = "钛媒体"
        self.label = "著名公司"

    def crawl(self):
        try:
            page = 1
            while not DaGongSi.update_stop:
                resp = requests.get(url=self.page_url % page, headers=DaGongSi.headers)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("div", class_="mod-article-list clear").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h3").find("a")
                        title = href.get("title")
                        url = DaGongSi.site_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            DaGongSi.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img").get("src")
                        rel_date = article.find("span", class_="author")
                        self.extract(rel_date.find("a"))
                        self.extract((rel_date.find("span", class_="gap-point")))
                        rel_date = rel_date.get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            DaGongSi.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("TaiMeiTi crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("TaiMeiTi crawl error. ErrMsg: %s" % str(e))
        finally:
            DaGongSi.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="inner")
        # 删除文章中不必要的
        p = article_body.find("p", attrs={"style": "text-align: center;"})
        self.extract(p)
        for item in p.next_siblings:
            self.extract(item)
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    def insert_line(self, result, item):
        if len(item.get_text()) > 0:
            result.append({"type": "text", "data": item.__str__() + "<br />"})

    @staticmethod
    def convert_date(date_str):
        try:
            date_str = Crawler.replace_white_space(date_str)
            time_format = "%Y-%m-%d%H:%M"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in TaiMeiTi. ErrMsg: %s" % str(e))


class English(DaGongSi):

    def __init__(self):
        super().__init__()
        self.label = "英文"
        self.page_url = "http://www.tmtpost.com/column/2573634/%s"


class QuKuaiLian(DaGongSi):

    def __init__(self):
        super().__init__()
        self.label = "商业资讯"
        self.page_url = "http://www.tmtpost.com/column/3015019/%s"


class ChuangTou(DaGongSi):

    def __init__(self):
        super().__init__()
        self.label = "商业新闻"
        self.page_url = "http://www.tmtpost.com/column/2446155/%s"


class WenYuShengHuo(DaGongSi):

    def __init__(self):
        super().__init__()
        self.label = "电影"
        self.page_url = "http://www.tmtpost.com/column/2446157/%s"


class QiCheChuXing(DaGongSi):

    def __init__(self):
        super().__init__()
        self.label = "商业资讯"
        self.page_url = "http://www.tmtpost.com/column/2573550/%s"


def crawl():
    items = [DaGongSi(), English(), ChuangTou(), WenYuShengHuo(), QiCheChuXing()]
    for item in items:
        item.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


