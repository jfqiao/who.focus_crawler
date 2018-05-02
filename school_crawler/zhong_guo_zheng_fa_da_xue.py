# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import json
import bs4

import school_crawler.convert_file as convert_util
from website_crawler.crawler import Crawler


class JiaoWuChu(Crawler):

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    website_url = "http://jwc.cupl.edu.cn"

    def __init__(self):
        self.page_url = "http://jwc.cupl.edu.cn/index/tzgg.htm"
        self.origin = "中国政法大学"
        self.label = ""
        self.p_label = "教务处"
        self.output_url = None

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

    def crawl(self):
        try:
            page = 20
            while not JiaoWuChu.update_stop:
                if page == 20:
                    url = self.page_url
                else:
                    url = "http://jwc.cupl.edu.cn/index/tzgg/%s.htm" % page
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    break
                # return
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("div", class_="list major").find("ul").findAll("li")
                if len(articles_list) == 0:
                    return
                for article in articles_list:
                    try:
                        self.label = self.p_label + "-" + article.find("a").get_text()[1:-2]
                        href = article.find("a", class_="title")
                        title = href.get_text()
                        if page == 20:
                            url = self.website_url + href.get("href")[2:]              # url有一个".."回退。
                        else:
                            url = self.website_url + href.get("href")[5:]
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            # JiaoWuChu.update_stop = 1  # 如果有则可以直接停止
                            continue
                        image_url = "https://gss3.bdstatic.com/7Po3dSag_xI4khGkpoWK1HF6hhy/baike/c0%3Dbaike80%2C5%2C" \
                                    "5%2C80%2C26/sign=82ddde93a786c9171c0e5a6ba8541baa/7af40ad162d9f2d3403b1e84a9ec8a" \
                                    "136327ccb6.jpg"                       # 没有图片
                        rel_date = article.find("span").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            JiaoWuChu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.output_url = url      # used to the image file name
                        self.get_article_content(url)
                        # self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
                page -= 1
        except BaseException as e:
            print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
        finally:
            JiaoWuChu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, timeout=5)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="content")
        content = self.parse_content(article_body)
        if article_html.find("ul", style="list-style-type:none;"):
            content.append({"type": "text", "data": "<p>相关附件下载请移步官网。<p>"})
        content = json.dumps(content).encode("UTF-8").decode("UTF-8")
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    @staticmethod
    def convert_date(date_str):
        try:
            time_format = "%Y-%m-%d"
            date = datetime.datetime.strptime(date_str, time_format)
            return date
        except BaseException as e:
            print("Convert time error in ZhongGuoZhengFaDaXue. ErrMsg: %s" % str(e))

    def parse_content(self, bs_obj):
        count_image = 0
        result = []
        items = bs_obj.descendants
        for item in items:
            if type(item) == bs4.element.NavigableString:
                continue
            # p标签以及对立的span标签都是需要的，但是p标签可能包含span标签
            if item.name == "p":
                if item.find("img") is None and self.check_table_parent(item):
                    self.insert_line(result, item)
            elif item.name == "img":
                src = self.website_url + item.get("src")
                result.append({"type": "image", "data": src})
            elif item.name == "span":
                if self.check_parent(item) and self.check_table_parent(item):
                    self.insert_line(result, item)
            elif item.name == "table":
                output_image_file_name = self.output_url.replace(":", "").replace("/", "") + ".jpg"
                if count_image > 0:
                    output_image_file_name = str(count_image) + output_image_file_name
                src_html = item.__str__()
                convert_result = convert_util.convert_html_to_image(src_html, Crawler.write_image_path + "/"
                                                                    + output_image_file_name)
                if convert_result:
                    result.append({"type": "image", "data": Crawler.image_url + output_image_file_name})
                    count_image += 1
                    txt_output_image = Crawler.write_image_path + "/" + output_image_file_name + ".txt"
                    f = open(txt_output_image, "wt")
                    f.write("image/jpg")
                    f.flush()
                    f.close()
                else:
                    result.append({"type": "text", "data": item.__str__()})
        return result
        # return json.dumps(result).encode("UTF-8").decode("UTF-8")


class XinWenDongTai(JiaoWuChu):

    def __init__(self):
        super().__init__()
        self.page_url = "http://jwc.cupl.edu.cn/index/xwdt.htm"


class XueShengChu(JiaoWuChu):

    def __init__(self):
        super().__init__()
        self.page_url = "http://xsc.cupl.edu.cn/tzgg.htm"
        self.label = "学生处"
        self.website_url = "http://xsc.cupl.edu.cn"

    def crawl(self):
        try:
            page = 49
            while not JiaoWuChu.update_stop:
                if page == 49:
                    url = self.page_url
                else:
                    url = "http://xsc.cupl.edu.cn/tzgg/%s.htm" % page
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    # break
                    return
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("ul", class_="newsList_news_1").findAll("li")
                if len(articles_list) == 0:
                    return
                for article in articles_list:
                    try:
                        href = article.find("a")
                        title = href.get_text()
                        if page == 49:
                            url = self.website_url + "/" + href.get("href")             # url有一个".."回退。
                        else:
                            url = self.website_url + href.get("href")[2:]
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            JiaoWuChu.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = "https://gss3.bdstatic.com/7Po3dSag_xI4khGkpoWK1HF6hhy/baike/c0%3Dbaike80%2C5%2C" \
                                    "5%2C80%2C26/sign=82ddde93a786c9171c0e5a6ba8541baa/7af40ad162d9f2d3403b1e84a9ec8a" \
                                    "136327ccb6.jpg"                       # 没有图片
                        rel_date = article.find("span").get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            JiaoWuChu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        # self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
                page -= 1
        except BaseException as e:
            print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
        finally:
            JiaoWuChu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, timeout=5)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", id="vsb_content")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)


class JiuYeChuangYe_TongZhi(JiaoWuChu):

    def __init__(self):
        super().__init__()
        self.website_url = "http://career.cupl.edu.cn"
        self.page_url = "http://career.cupl.edu.cn/openinfo/news?pid=107813&page=%s"
        self.label = "就业创业-通知"

    def crawl(self):
        try:
            page = 1
            while not JiaoWuChu.update_stop:
                resp = requests.get(self.page_url % page, timeout=5)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("ul", class_="contentR_list").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("a")
                        title = href.get_text()
                        url = self.website_url + href.get("href")             # url有一个".."回退。
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            JiaoWuChu.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = "https://gss3.bdstatic.com/7Po3dSag_xI4khGkpoWK1HF6hhy/baike/c0%3Dbaike80%2C5%2C" \
                                    "5%2C80%2C26/sign=82ddde93a786c9171c0e5a6ba8541baa/7af40ad162d9f2d3403b1e84a9ec8a" \
                                    "136327ccb6.jpg"                       # 没有图片
                        rel_date = article.findAll("span")[1].get_text()
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            JiaoWuChu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        date_str = date.strftime(Crawler.time_format)
                        self.get_article_content(url)
                        # self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date_str,
                                                 date_str, self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
        finally:
            JiaoWuChu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, timeout=5)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", class_="contR_xq")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)


class JiuYeChuangYe_ShiXi(JiuYeChuangYe_TongZhi):

    def __init__(self):
        super().__init__()
        self.label = "就业创业-实习"
        self.page_url = "http://career.cupl.edu.cn/openinfo/news?pid=107817&page=%s"


class JiuYeChuangYe_JiuYe(JiuYeChuangYe_TongZhi):

    def __init__(self):
        super().__init__()
        self.label = "就业创业-就业"
        self.page_url = "http://career.cupl.edu.cn/openinfo/news?pid=107816&page=%s"


class JiuYeChuangYe_ZhuanChangZhaoPinHui(JiuYeChuangYe_TongZhi):

    def __init__(self):
        super().__init__()
        self.label = "就业创业-招聘会"
        self.page_url = "http://career.cupl.edu.cn/openinfo/jobmeet?pid=&page=%s"


class DangWei(JiaoWuChu):

    def __init__(self):
        super().__init__()
        self.website_url = "http://zzb.cupl.edu.cn"
        self.page_url = "http://zzb.cupl.edu.cn/bmgg.htm"
        self.label = "党委组织部"

    def crawl(self):
        try:
            resp = requests.get(self.page_url, timeout=5)
            if resp.status_code != 200:
                return
            bs_obj = BeautifulSoup(resp.content, "html.parser")
            articles_list = bs_obj.find("div", class_="newslist newlist_list").find("ul").findAll("li")
            if len(articles_list) == 0:
                return
            for article in articles_list:
                try:
                    href = article.find("a")
                    title = href.get_text()
                    url = self.website_url + "/" + href.get("href")             # url有一个".."回退。
                    select_result = self.select_url(url)
                    if select_result:  # 查看数据库是否已经有该链接
                        JiaoWuChu.update_stop = 1  # 如果有则可以直接停止
                        break
                    image_url = "https://gss3.bdstatic.com/7Po3dSag_xI4khGkpoWK1HF6hhy/baike/c0%3Dbaike80%2C5%2C" \
                                "5%2C80%2C26/sign=82ddde93a786c9171c0e5a6ba8541baa/7af40ad162d9f2d3403b1e84a9ec8a" \
                                "136327ccb6.jpg"                       # 没有图片
                    rel_date = article.find("span").get_text()
                    # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                    date = self.convert_date(rel_date)
                    if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                        JiaoWuChu.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                        break
                    date_str = date.strftime(Crawler.time_format)
                    self.get_article_content(url)
                    # self.crawl_image_and_save(image_url)
                    self.write_data_to_sheet(title, url, image_url, date_str,
                                             date_str, self.label, self.origin)
                    self.insert_url(url)
                    print(url)
                except BaseException as e:
                    print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
                # page -= 1
        except BaseException as e:
            print("ZhongGuoZheFaDaXue crawl error. ErrMsg: %s" % str(e))
        finally:
            JiaoWuChu.update_stop = 0    # 重置为开始状态，为后续爬其他模块做准备。

    def get_article_content(self, url):
        resp = requests.get(url, timeout=5)
        article_html = BeautifulSoup(resp.content, "lxml")
        article_body = article_html.find("div", id="vsb_content")
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)


class XueShengHui(Crawler):
    # 微信公众号: 账号主体为个人，无法使用搜狗检索。
    pass


def crawl():
    Crawler.initialize_workbook()
    JiaoWuChu().crawl()
    # XueShengChu().crawl()
    # JiuYeChuangYe_TongZhi().crawl()
    # JiuYeChuangYe_JiuYe().crawl()
    # JiuYeChuangYe_ShiXi().crawl()
    # JiuYeChuangYe_ZhuanChangZhaoPinHui().crawl()
    # DangWei().crawl()
    Crawler.save_workbook()


if __name__ == "__main__":
    # 注意运行中国政法大学需要调整数据库为db_WhoFocus_final
    # Crawler.initialize_workbook()
    crawl()
    # Crawler.save_workbook()


