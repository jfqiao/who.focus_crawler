import requests
from bs4 import BeautifulSoup
import xlwt
import datetime
from db_util import DBUtil
from wechat_crawler import WechatArticleCrawler
import sys
from website_crawler.crawler import Crawler

import re


class XiGuaCrawler(object):

    need_crawl_tag = ["商业资讯", "社会观点", "校园学习", "时尚", "体育", "电影", "游戏", "趣味", "读书"]

    insert_sql_format = "INSERT INTO t_article_url(url, insert_time) VALUES(\"%s\", \"%s\")"

    select_sql_format = "SELECT * FROM t_article_url WHERE url = \"%s\""

    # global line count
    line_count = 0

    # 将cookie字符串转换为字典
    cookies_dict = {}

    # 直接登录后拿到的cookie, 以后需要模拟登录拿数据
    cookies_str = 'LoginTag=a9c2d09d95da4e668a9730d103fa4ff9; _XIGUASTATE=XIGUASTATEID=b9046bc650534e7bb8325da9000c58ce; ASP.NET_SessionId=n4llk4tgfij3djdbvubjwugm; _XIGUA=UserId=d471a30ba6f3c365&Account=fd0673b157bef6e1f2b65e9f22a7aed8&checksum=4be8ae8c72b3; LV2=1; ExploreTags672571=; SERVERID=2e7fd5d7f4caba1a3ae6a9918d4cc9a6|1521172561|1521165343; _chl=key=BaiduOrginal; Hm_lvt_72aa476a79cf5b994d99ee60fe6359aa=1520737791,1523155884; Hm_lpvt_72aa476a79cf5b994d99ee60fe6359aa=1523155889; Big3Biz672571=False; ShowOneKeyAsyncTip=1'

    enter_url = "http://zs.xiguaji.com/MArticle/Attention"

    tag_article_url = "http://zs.xiguaji.com/MArticle/Attention/?tags=%s&position=2"

    # 用来获取每一页的URL，有的标签下只有一页，有的标签下有多页。
    page_url_format = "http://zs.xiguaji.com/MArticle/Attention/?position=2&dayInterval=0.08&articleType=-1&tags=%s&onlyTopLine=&page=%d&more=1"

    # datInterval 表示时间取值， 1表示最近24小时，0.08表示最近12小时，3表示最近3天

    # 西瓜爬文章的逻辑：设置登录cookie，从enter-url进入，然后获取每个分组的消息。首先拿到每个分组的tagID，然后根据tag_article_url请求更多

    articles_dir = Crawler.base_dir + "xi_gua_articles/"

    line_format = "%s,%s,%s,%s,%s,%s"

    file_path = ""

    @staticmethod
    def set_cookie_dict():
        strs = XiGuaCrawler.cookies_str.split(";")
        for string in strs:
            pos = string.index("=")
            key = string[:pos].replace(" ", "")
            value = string[pos + 1:].replace(" ", "")
            XiGuaCrawler.cookies_dict[key] = value

    @staticmethod
    def xi_gua_crawl():
        XiGuaCrawler.set_cookie_dict()
        file_name = XiGuaCrawler.articles_dir + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        XiGuaCrawler.file_path = file_name + ".xls"
        write_workbook = xlwt.Workbook(encoding="ascii")
        write_sheet = write_workbook.add_sheet("articles")
        XiGuaCrawler.write_sheet_write(write_sheet, XiGuaCrawler.line_count, "标题", "链接", "图片链接", "标签",
                                       "来源", "发布时间（绝对）", "发布时间（相对）")
        XiGuaCrawler.set_cookie_dict()
        r = requests.get(XiGuaCrawler.enter_url, cookies=XiGuaCrawler.cookies_dict)
        serverid = r.cookies.get("SERVERID")
        XiGuaCrawler.cookies_dict["SERVERID"] = serverid
        bs_obj = BeautifulSoup(r.content, "lxml")
        tags = bs_obj.find("ul", id="ulMyTagList").findAll("li", attrs={"data-loaded": re.compile("[01]")})
        tags_dict = {}
        for li_tag in tags:
            tag_name = li_tag.get("data-tagname")
            tag_id = li_tag.get("data-tagid")
            tags_dict[tag_name] = tag_id
        keys = tags_dict.keys()
        for key in keys:
            if key not in XiGuaCrawler.need_crawl_tag:
                continue
            print(key)
            XiGuaCrawler.craw_tag(key, tags_dict.get(key), write_sheet)
        write_workbook.save(file_name + ".xls")

    @staticmethod
    def write_sheet_write(write_sheet, line_count, title, link, image_link, tag, origin, rel_time, standard_time):
        write_sheet.write(line_count, 0, title)
        write_sheet.write(line_count, 1, link)
        write_sheet.write(line_count, 2, image_link)
        write_sheet.write(line_count, 3, tag)
        write_sheet.write(line_count, 4, origin)
        write_sheet.write(line_count, 5, standard_time)
        write_sheet.write(line_count, 6, rel_time)

    @staticmethod
    def craw_tag(tag_name, tag_id, write_sheet):
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        page = 1
        while 1:
            url = XiGuaCrawler.page_url_format % (tag_id, page)
            r = requests.get(url, cookies=XiGuaCrawler.cookies_dict)
            serverid = r.cookies.get("SERVERID")
            XiGuaCrawler.cookies_dict["SERVERID"] = serverid
            if len(r.content) < 100:      # page页面没有了之后返回的长度是24
                break
            bs_obj = BeautifulSoup(r.content, "html.parser")
            article_tags = bs_obj.findAll("tr", attrs={"data-articleid": re.compile(".*")})
            for article_tag in article_tags:
                title_tag = article_tag.find("div", class_="mp-article-title")
                href_tag = title_tag.find("a")
                title = href_tag.get_text().replace("\n", "")
                link = href_tag.get("href")
                # 利用数据库保存已有的链接，如果没有在数据库中，插入数据库，并写入文件，否则不插入数据库，也不写入文件。
                if DBUtil.select_data(XiGuaCrawler.select_sql_format % link) is None:
                    DBUtil.insert_data(XiGuaCrawler.insert_sql_format % (link, time_str))
                    source_tag = article_tag.find("div", class_="item-source")
                    origin = source_tag.find("div", class_="item-title").get_text()
                    rel_time = source_tag.find("div", class_="item-sub-title").get_text()
                    standard_time = XiGuaCrawler.convert_time_to_standard_time(rel_time)
                    XiGuaCrawler.line_count += 1
                    XiGuaCrawler.write_sheet_write(write_sheet, XiGuaCrawler.line_count, title, link, "",
                                                   tag_name, origin, rel_time, standard_time)
            page += 1

    @staticmethod
    def convert_time_to_standard_time(rel_time):
        '''
        将XX小时或分钟前这种相对时间转化为标准时间。yyyy-mm-dd HH:MM:SS
        :param rel_time:
        :return:
        '''
        cur_time = datetime.datetime.now()

        if "小时" in rel_time:
            pos = rel_time.find(" ")
            hours = int(rel_time[:pos])
            time_delta = datetime.timedelta(hours=hours)
        elif "分钟" in rel_time:
            pos = rel_time.find(" ")
            minutes = int(rel_time[:pos])
            time_delta = datetime.timedelta(minutes=minutes)
        else:
            time_delta = datetime.timedelta(seconds=0)
        cur_time -= time_delta
        return cur_time.strftime("%Y-%m-%d %H:00:00")


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    XiGuaCrawler.xi_gua_crawl()
    WechatArticleCrawler.get_url_and_set(XiGuaCrawler.file_path)
