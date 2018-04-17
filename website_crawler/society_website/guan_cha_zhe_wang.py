# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time

from website_crawler.crawler import Crawler


class YaoWen(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    website_url = "http://www.guancha.cn"

    def __init__(self):
        self.page_url = "http://www.guancha.cn/mainnews-yw/list_%s.shtml"
        self.origin = "观察者网"
        self.label = "社会"
        self.image_url = "https://ss2.baidu.com/6ONYsjip0QIZ8tyhnq/it/u=3468702903,882974955&" \
                         "fm=58&s=1FE6D916CCF542905376B7F40300703E"

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 1
            while not YaoWen.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "lxml")
                articles_list = bs_obj.find("ul", class_="new-left-list").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h4").find("a")
                        title = href.get_text()
                        url = YaoWen.website_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            YaoWen.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img").get("src")
                        rel_date = article.find("div", class_="module-interact").find("span").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YaoWen.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
        finally:
            YaoWen.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="content all-txt")
        # 删除文章中不必要的
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%d %H:%M:%S"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in GuanChaZheWang. ErrMsg: %s" % str(e))


class TouTiao(YaoWen):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.guancha.cn/GuanChaZheTouTiao/list_%s.shtml"

    def crawl(self):
        try:
            page = 1
            while not YaoWen.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "lxml")
                articles_list = bs_obj.find("ul", class_="headline-list fix").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h3").find("a")
                        title = href.get_text()
                        url = YaoWen.website_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            YaoWen.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img").get("src")
                        rel_date = article.find("div", class_="module-interact").find("span").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YaoWen.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
        finally:
            YaoWen.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。


class GuoJi(YaoWen):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.guancha.cn/GuoJi%%C2%%B7ZhanLue/list_%s.shtml"

    def crawl(self):
        try:
            page = 1
            while not YaoWen.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "lxml")
                articles_list = bs_obj.find("ul", class_="column-list fix").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h4").find("a")
                        title = href.get_text()
                        url = YaoWen.website_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            YaoWen.update_stop = 1  # 如果有则可以直接停止
                            break
                        rel_date = article.find("div", class_="module-interact").find("span").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YaoWen.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        image_url = self.get_article_content(url)
                        if len(image_url) == 0:
                            image_url = self.image_url
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
        finally:
            YaoWen.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="content all-txt")
        # 删除文章中不必要的
        imgs = article_body.findAll("img")
        if len(imgs) == 0:
            return ""
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)
        return imgs[0].get("src")


class ShePing(GuoJi):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.guancha.cn/mainnews-sp/list_%s.shtml"

    def crawl(self):
        try:
            page = 1
            while not YaoWen.update_stop:
                resp = requests.get(url=self.page_url % page)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "lxml")
                articles_list = bs_obj.find("ul", class_="review-list").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h4").find("a")
                        title = href.get_text()
                        url = YaoWen.website_url + href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            YaoWen.update_stop = 1  # 如果有则可以直接停止
                            break
                        rel_date = article.find("div", class_="module-interact").find("span").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YaoWen.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        image_url = self.get_article_content(url)
                        if len(image_url) == 0:
                            image_url = self.image_url
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("GuanChaZheWang crawl error. ErrMsg: %s" % str(e))
        finally:
            YaoWen.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。


class ZhongGuoJingJi(GuoJi):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.guancha.cn/zhongguojingji/list_%s.shtml"


class ITXinLangChao(GuoJi):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.guancha.cn/ITXinLangChao/list_%s.shtml"


class KeJi(GuoJi):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.guancha.cn/KeJi/list_%s.shtml"


def crawl():
    cyb = YaoWen()
    cyb.crawl()
    tt = TouTiao()
    tt.crawl()
    gj = GuoJi()
    gj.crawl()
    sp = ShePing()
    sp.crawl()
    zgjj = ZhongGuoJingJi()
    zgjj.crawl()
    xlc = ITXinLangChao()
    xlc.crawl()
    kj = KeJi()
    kj.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()


