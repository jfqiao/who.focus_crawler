# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import json
import bs4

from website_crawler.crawler import Crawler


class RenMinWang(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    website_url = "http://society.people.com.cn"

    def __init__(self):
        self.page_url = "http://society.people.com.cn/GB/86800/index%s.html"
        self.origin = "人民网"
        self.label = "社会新闻"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not RenMinWang.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("ul", class_="list_14 clearfix").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("a")
                        title = href.get_text()
                        url = RenMinWang.website_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            RenMinWang.update_stop = 1  # 如果有则可以直接停止
                            break
                        rel_date = article.find("i", class_="gray").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            RenMinWang.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        image_url = self.get_article_content(url)
                        if len(image_url) == 0:
                            continue
                        image_url = RenMinWang.website_url + image_url
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("RenMinWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("RenMinWang crawl error. ErrMsg: %s" % str(e))
        finally:
            RenMinWang.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="box_con")
        self.extract(article_body.find("div", class_="jingbian2012"))
        imgs = article_body.findAll("img")
        if len(imgs) <= 0:
            return ""
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)
        return imgs[0].get("src")

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y %m月%d日 %H:%S "
            date = datetime.datetime.strptime("2018" + date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in RenMinWang. ErrMsg: %s" % str(e))

    def parse_content(self, bs_obj):
        result = []
        items = bs_obj.descendants
        for item in items:
            if type(item) == bs4.element.NavigableString:
                continue
            # p标签以及对立的span标签都是需要的，但是p标签可能包含span标签
            if item.name == "p":
                if item.find("img") is None:
                    # f.write(item.__str__())
                    self.insert_line(result, item)
            elif item.name == "img":
                src = item.get("data-src")
                if src is None or len(src) == 0:
                    src = item.get("src")
                class_list = item.get("class")
                if class_list is not None and "__bg_gif" in item.get("class"):  # 去除掉一些背景gif图片
                    continue
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
                result.append({"type": "image", "data": RenMinWang.website_url + src})
            elif item.name == "span":
                if self.check_parent(item):
                    self.insert_line(result, item)
                    # result.append({"type": "text", "data": item.__str__()})
        return json.dumps(result).encode("UTF-8").decode("UTF-8")

def crawl():
    # hy = HangYe("fintech")   # 文章都没有图片
    # hy.crawl()
    rmw = RenMinWang()
    rmw.crawl()


if __name__ == "__main__":
    # Crawler.initialize_workbook()
    crawl()
    # Crawler.save_workbook()


