# coding=utf-8
import requests
from bs4 import BeautifulSoup
import bs4
import datetime
import json

from website_crawler.crawler import Crawler


class YuLe(Crawler):

    page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=63&page=%s"

    update_stop = 0  # stop crawler.

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"}

    def __init__(self):
        self.origin = "界面"
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=76&page=%s"
        self.label = "娱乐"

    def crawl(self):
        try:
            page = 1
            while not YuLe.update_stop:
                resp = requests.get(url=YuLe.page_url % page, headers=YuLe.headers)
                if resp.status_code != 200:
                    continue
                json_content = resp.content.decode("utf-8")[1:-1]
                json_obj = json.loads(json_content)
                bs_obj = BeautifulSoup(json_obj.get("rst"), "html.parser")
                articles_list = bs_obj.findAll("div", class_="news-view left card")
                if len(articles_list) == 0:
                    break
                for article in articles_list:
                    try:
                        href = article.find("h3").find("a")
                        title = href.get_text().replace("\n", "")
                        url = href.get("href")
                        select_result = self.select_url(url)
                        if select_result:  # 查看数据库是否已经有该链接
                            # YuLe.update_stop = 1  # 如果有则可以直接停止
                            continue
                        image_url = article.find("img").get("src").replace("img1", "img").replace("img2", "img")\
                            .replace("img3", "img")
                        if "http:" not in image_url:
                            image_url = "http:" + image_url
                        rel_date = article.find("span", class_="date").get_text()
                        date = self.convert_date(rel_date)
                        if date < self.target_date:  # 比较文章的发表时间，可以保留特定时间段内的文章
                            YuLe.update_stop = 1  # 如果文章的发表时间在给定的时间之前，则停止爬虫
                            break
                        self.get_article_content(url)
                        self.crawl_image_and_save(image_url)
                        self.write_data_to_sheet(title, url, image_url, date.strftime("%Y-%m-%d %H:%M"), rel_date,
                                                 self.label, self.origin)
                        self.insert_url(url)
                        print(url)
                    except BaseException as e:
                        print("JieMian crawl error. ErrMsg:%s" % str(e))
                page += 1
        except BaseException as e:
            print("JieMian crawl error. ErrMsg:%s" % str(e))

    def get_article_content(self, url):
        resp = requests.get(url, headers=YuLe.headers)
        article_html = BeautifulSoup(resp.content, "html.parser")
        article_body = article_html.find("div", class_="article-main")
        # 删除文章中不必要的不分
        self.extract(article_body.find("p", class_="report-view"))
        content = self.parse_content(article_body)
        self.save_file(content, url)
        self.save_abstract(article_body, url)

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
                if "http:" not in src:
                    src = "http:" + src
                src = src.replace("img1", "img").replace("img2", "img").replace("img3", "img")
                result.append({"type": "image", "data": src})
            elif item.name == "span":
                if self.check_parent(item):
                    self.insert_line(result, item)
                    # result.append({"type": "text", "data": item.__str__()})
        return json.dumps(result).encode("UTF-8").decode("UTF-8")

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
                mins = int(date_str.replace("分钟前", ""))
                time_gap = datetime.timedelta(minutes=mins)
                date = datetime.datetime.now() - time_gap
            elif "小时" in date_str:
                hours = int(date_str.replace("小时前", ""))
                time_gap = datetime.timedelta(hours=hours)
                date = datetime.datetime.now() - time_gap
            elif "今天" in date_str:
                time = date_str.replace("今天", "")
                date = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d-") + time,
                                                  "%Y-%m-%d-%H:%M")
            elif "昨天" in date_str:
                time = date_str.replace("昨天", "")
                date = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d-") + time,
                                                  "%Y-%m-%d-%H:%M") - datetime.timedelta(days=1)
            else:
                date = datetime.datetime.strptime("2018-" + date_str, "%Y-%m/%d%H:%M")    # 这里确定是2018年的文章
            return date
        except BaseException as e:
            print("JieMain crawler error in convert time. Time String : %s. ErrMsg: %s" % (date_str, str(e)))


class HongGuan(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=174&page=%s"
        self.label = "财经新闻"


class TiYu(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=82&page=%s"
        self.label = "体育"


class ShiShang(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=68&page=%s"
        self.label = "时尚"


class WenHua(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=130&page=%s"
        self.label = "读书"


class YouXi(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=118&page=%s"
        self.label = "游戏"


class ShuJu(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=154&page=%s"
        self.label = "商业资讯"


class KeJi(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=65&page=%s"
        self.label = "科技"


class ZhengQuan(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=112&page=%s"
        self.label = "财经新闻"


class JinRong(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=9&page=%s"
        self.label = "商业资讯"


class XiaoFei(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=31&page=%s"
        self.label = "著名公司"


class YingXiao(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=49&page=%s"
        self.label = "商业资讯"


class GuanLi(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=139&page=%s"
        self.label = "商业观点"


class ChuangYe(YuLe):

    def __init__(self):
        super().__init__()
        self.page_url = "https://a.jiemian.com/index.php?m=lists&a=ajaxlist&cid=141&page=%s"
        self.label = "创业干货"

        
def crawl():
    items = [YuLe(), HongGuan(), TiYu(), ShiShang(), WenHua(), YouXi(), ShuJu(), KeJi(), ZhengQuan(), JinRong(),
             XiaoFei(), YingXiao(), GuanLi(), ChuangYe()]
    for item in items:
        item.crawl()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    crawl()
    Crawler.save_workbook()
