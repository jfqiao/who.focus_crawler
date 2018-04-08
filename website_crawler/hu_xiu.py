# coding=utf-8
import requests
from bs4 import BeautifulSoup
import json
import datetime
import re

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

    data = {"page": "", "huxiu_hash_code": "", "last_dateline": ""}

    def __init__(self):
        self.origin = "虎嗅"
        self.label = "商业资讯"

    def crawl(self):
        try:
            page = 0
            while not HuXiuCrawler.update_stop:
                if page == 0:
                    url = HuXiuCrawler.huxiu_site_url
                    resp = requests.get(url, headers=HuXiuCrawler.headers)
                    content = resp.content
                else:
                    url = HuXiuCrawler.post_url
                    HuXiuCrawler.data["page"] = str(page)
                    resp = requests.post(url=url, headers=HuXiuCrawler.headers, data=HuXiuCrawler.data)
                    if resp.status_code != 200:
                        continue
                    obj = json.loads(resp.content)
                    content = obj.get("data")
                    HuXiuCrawler.data["last_dateline"] = obj.get("last_dateline")
                bs_obj = BeautifulSoup(content, "lxml")
                if page == 0:
                    pattern = re.compile("huxiu_hash_code='(.*)';")
                    mat_obj = re.search(pattern, bs_obj.find("script", attrs={"type": "text/javascript"}).get_text())
                    HuXiuCrawler.data["huxiu_hash_code"] = mat_obj.group(1)
                    date = bs_obj.find("div", attrs={"data-last_dateline": re.compile(".*")})
                    HuXiuCrawler.data["last_dateline"] = date.get("data-last_dateline")
                articles_list = bs_obj.findAll("div", attrs={"class": re.compile("mod-b mod-art.*")})
                for article in articles_list:
                    try:
                        href = article.find("h2").find("a")
                        title = href.get_text().replace("\n", "")  # title should not contains new line
                        url = HuXiuCrawler.huxiu_site_url + href.get("href")  # 相对链接
                        select_result = self.select_url(url)
                        if select_result:                                                      # 查看数据库是否已经有该链接
                            # HuXiuCrawler.update_stop = 1                                       # 如果有则可以直接停止
                            continue
                        image_url = article.find("img").get("data-original")             # 图片标签，地址在data-originalsh属性下
                        rel_date = article.find("span", class_="time").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:    # 比较文章的发表时间，可以保留特定时间段内的文章
                            HuXiuCrawler.update_stop = 1       # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        # label = article.find("a", class_="column-link").get("text")
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date.strftime("%Y-%m-%d %H:%M"), rel_date,
                                                 self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("HuXiu crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("HuXiu crawl error. ErrMsg: %s" % str(e))

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__()})

    def get_article_content(self, url):
        resp = requests.get(url, headers=HuXiuCrawler.headers)
        article_html = BeautifulSoup(resp.content, "html.parser")
        article_body = article_html.find("div", class_="article-wrap")
        # 删除文章中不必要的不分
        self.extract(article_body.find("h1", class_="t-h1"))
        self.extract(article_body.find("div", class_="article-author"))
        self.extract(article_body.find("div", class_="neirong-shouquan"))
        self.extract(article_body.find("div", class_="neirong-shouquan-public"))
        self.extract(article_body.find("div", class_="Qr-code"))
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
            print("HuXiu crawler error in convert time. Time String : %s. ErrMsg: %s" % (date_str, str(e)))


def crawl():
    hx = HuXiuCrawler()
    hx.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()
