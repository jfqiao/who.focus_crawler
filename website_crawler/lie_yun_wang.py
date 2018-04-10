# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime

from website_crawler.crawler import Crawler


class ZaoQiXiangMu(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    site_url = "http://www.lieyunwang.com"

    def __init__(self):
        self.page_url = "http://www.lieyunwang.com/c/pioneer/p%s.html"
        self.origin = "猎云网"
        self.label = "商业资讯"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not ZaoQiXiangMu.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.findAll("div", class_="article-bar clearfix")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("div", class_="article-info pore").find("a")
                        title = href.get_text()
                        url = ZaoQiXiangMu.site_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            ZaoQiXiangMu.update_stop = 1  # 如果有则可以直接停止
                            break                      # 有可能有的标签下有相同的文章，因此不用记录即可。以时间作为停止标准
                        image_url = article.find("img").get("src")
                        rel_date = article.find("span", class_="timestamp").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            ZaoQiXiangMu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("LieYunWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("LieYunWang crawl error. ErrMsg: %s" % str(e))
        finally:
            ZaoQiXiangMu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="main-text")
        self.extract(article_body.find("span", class_="poperweima"))
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
            print("LieYunWang crawler error in convert time. Time String : %s. ErrMsg: %s" % (date_str, str(e)))


class QuKuaiLian(ZaoQiXiangMu):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.lieyunwang.com/c/blockchain/p%s.html"
        self.label = "商业资讯"


class DaSongSi(ZaoQiXiangMu):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.lieyunwang.com/c/internet/p%s.html"
        self.label = "著名公司"


class RenWu(ZaoQiXiangMu):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.lieyunwang.com/c/people/p%s.html"
        self.label = "商业观点"


class RongZiHui(ZaoQiXiangMu):

    def __init__(self):
        super().__init__()
        self.label = "商业资讯"
        self.page_url = "http://www.lieyunwang.com/c/weeklyinvest/p%s.html"


def crawl():
    zqxm = ZaoQiXiangMu()
    zqxm.crawl()
    qkl = QuKuaiLian()
    qkl.crawl()
    dgs = DaSongSi()
    dgs.crawl()
    rw = RenWu()
    rw.crawl()
    rzh = RongZiHui()
    rzh.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


