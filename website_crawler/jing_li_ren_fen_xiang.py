# coding=utf-8
import requests
from bs4 import BeautifulSoup
import datetime

from website_crawler.crawler import Crawler


class GuanLi(Crawler):

    manager_share_site_url = "http://www.managershare.com"

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.label = "商业观点"
        self.origin = "经理人分享"
        self.page_url = "http://www.managershare.com/column/1?page=%s"

    def crawl(self):
        try:
            page = 1
            while not GuanLi.update_stop:
                resp = requests.get(url=self.page_url % page, headers=GuanLi.headers)
                if resp.status_code != 200:
                    break
                bs_obj = BeautifulSoup(resp.content, "html.parser")
                articles_list = bs_obj.find("section", class_="post-list").findAll("li")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h3").find("a")
                        title = href.get_text().replace("\n", "")
                        url = GuanLi.manager_share_site_url + href.get("href")  # 相对链接
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            GuanLi.update_stop = 1  # 如果有则可以直接停止
                            break
                        image_url = article.find("img").get("data-original")
                        rel_date = self.replace_white_space(article.find("div", class_="post-meta").get_text())
                        # 文章发布的时间，一周以内是相对时间（天），今天的文章则相对时间为（时|分）， 其他时间则是绝对时间yyyy-mm-dd
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            GuanLi.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date.strftime("%Y-%m-%d %H:%M"), rel_date,
                                                 self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("JingLiRenFenXiang crawl error. ErrMsg: %s" % str(e))
                page += 1
        except BaseException as e:
            print("JingLiRenFenXiang crawl error. ErrMsg: %s" % str(e))

    def get_article_content(self, url):
        resp = requests.get(url, headers=GuanLi.headers)
        article_html = BeautifulSoup(resp.content, "html.parser")
        article_body = article_html.find("article", class_="post-content")
        # 删除文章中不必要的不分
        self.extract(article_body.find("div", class_="fn-clear post-bottom"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__() + "<br />"})

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
                time = date_str.replace("分钟前", "")
                time_gap = datetime.timedelta(minutes=int(time))
                date = datetime.datetime.now() - time_gap
            elif "时" in date_str:
                time = date_str.replace("小时前", "")
                hours = int(time)
                time_gap = datetime.timedelta(hours=hours)
                date = datetime.datetime.now() - time_gap
            elif "天" in date_str:
                time = date_str.replace("天前", "")
                time_gap = datetime.timedelta(days=int(time))
                date = datetime.datetime.now() - time_gap
            elif "年" in date_str:
                date = datetime.datetime.strptime(date_str, "%Y年%m月%d日")
            else:
                date = datetime.datetime.strptime("2018-" + date_str, "%Y-%m月%d日")    # 这里确定是2018年的文章
            return date
        except BaseException as e:
            print("JingLiRenFenXiang crawler error in convert time. Time String : %s. ErrMsg: %s" % (date_str, str(e)))


class YingXiao(GuanLi):

    def __init__(self):
        super().__init__()
        self.page_url = "http://www.managershare.com/column/2?page=%s"


def crawl():
    gl = GuanLi()
    gl.crawl()
    yx = YingXiao()
    yx.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()
