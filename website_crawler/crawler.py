# coding=utf-8
import os
import datetime
import xlwt
import bs4
import json
import requests

from db_util import DBUtil


class Crawler(object):
    """
    所有网站爬虫的父类，都需要继承这个类。
    需要实现的功能：
    1 保存爬取的信息到EXCEL文件中，文件名采用yyyy-mm-dd_HH-MM，保存文件到特定的文件夹下。
    2 保存爬的文章到特定文件夹中，如果文件夹不存在则创建文件夹，文件夹采用yyyy/mm/dd的形式,由于每天会爬多次，因此，还需要把每次
    不同的时间爬的数据保存在不通过的文件夹下，以方便传输到服务器上。
    调用顺序：
    1. 调用Crawler初始化workbook
    2. 调用爬虫爬数据
    3. Crawler保存workbook
    """

    base_dir = "/Users/jfqiao/Desktop/"

    is_article_dir_exists = 0     # 针对保存爬的文章的文件夹是否存在的标志，默认文件夹不存在，需要创建

    article_dir_parent =  base_dir + "wechat_articles/"       # 保存文章的根目录，

    article_dir_absolute = ""

    excel_result_dir = base_dir + "write_aritlce_dirs/"         # 保存爬的文章结果excel目录

    image_dir = base_dir + "image/"

    time_format = "%Y-%m-%d %H:%M:%S"

    workbook = None

    worksheet = None

    line_count = 0

    excel_file_name_pattern = "result_%Y-%m-%d_%H-%M"

    select_sql = "SELECT * FROM t_article_url WHERE url = \"%s\""

    insert_sql = "INSERT INTO t_article_url(url, insert_time) VALUES(\"%s\", \"%s\")"

    target_date = datetime.datetime.strptime("2018-04-12 23:59:59", "%Y-%m-%d %H:%M:%S")

    write_file_path = ""

    write_image_path = ""

    write_article_path = ""

    @staticmethod
    def save_workbook():
        date = datetime.datetime.now()
        file_name = date.strftime(Crawler.excel_file_name_pattern) + ".xls"
        Crawler.write_file_path = Crawler.excel_result_dir + file_name
        Crawler.workbook.save(Crawler.excel_result_dir + file_name)

    @staticmethod
    def initialize_workbook():
        Crawler.workbook = xlwt.Workbook(encoding="ascii")
        Crawler.worksheet = Crawler.workbook.add_sheet("articles")
        Crawler.write_data_to_sheet("标题", "链接", "图片链接", "发布时间（绝对）", "发布时间（对）", "标签", "来源")

    @staticmethod
    def write_data_to_sheet(title, url, image_link, abs_date, rel_date, label, origin):
        Crawler.worksheet.write(Crawler.line_count, 0, label=title)
        Crawler.worksheet.write(Crawler.line_count, 1, label=url)
        Crawler.worksheet.write(Crawler.line_count, 2, label=image_link)
        Crawler.worksheet.write(Crawler.line_count, 3, label=label)
        Crawler.worksheet.write(Crawler.line_count, 4, label=origin)
        Crawler.worksheet.write(Crawler.line_count, 5, label=abs_date)
        Crawler.worksheet.write(Crawler.line_count, 6, label=rel_date)
        Crawler.line_count += 1

    @staticmethod
    def save_file(content, url):
        try:
            if not Crawler.is_article_dir_exists:
                date = datetime.datetime.now()
                dir_created = date.strftime("%Y/%m/%d/%H_%M/")
                img_dir_created = date.strftime("%Y-%m-%d_%H-%M")
                Crawler.article_dir_absolute = Crawler.article_dir_parent + dir_created
                image_dir = Crawler.image_dir + img_dir_created
                Crawler.write_image_path = image_dir
                Crawler.write_article_path = Crawler.article_dir_absolute
                os.system("mkdir -p %s" % Crawler.article_dir_absolute)
                os.system("mkdir -p %s" % image_dir)
                Crawler.is_article_dir_exists = 1
            file_name = url.replace("/", "").replace(":", "")
            f = open(Crawler.article_dir_absolute + "/" + file_name, mode="w", encoding="utf-8")
            f.write(content)
            f.close()
        except BaseException as e:
            print("Save file error. ErrMsg: %s" % str(e))

    def crawl_image_and_save(self, image_url):
        # 在调用save_file后，调用此方法用于保存图片。
        file_name = image_url.replace(":", "").replace("/", "")
        pos = file_name.find("?")
        if pos > 0:
            file_name = file_name[:pos]
        resp = requests.get(image_url)
        content_type = resp.headers.get("Content-Type")
        f = open(Crawler.write_image_path + "/" + file_name, "wb")
        f.write(resp.content)
        f.close()
        f = open(Crawler.write_image_path + "/" + file_name + ".txt", "wt")
        f.write(content_type)
        f.close()

    @staticmethod
    def save_abstract(bs_obj, url):
        # 对于摘要需要将换行符去掉
        content = bs_obj.get_text()[:51].replace("\n", "")
        Crawler.save_file(content, url + "_abstract")

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
                result.append({"type": "image", "data": src})
            elif item.name == "span":
                if self.check_parent(item):
                    self.insert_line(result, item)
                    # result.append({"type": "text", "data": item.__str__()})
        return json.dumps(result).encode("UTF-8").decode("UTF-8")

    def insert_line(self, result, item):
        result.append({"type": "text", "data": item.__str__()})

    @staticmethod
    def check_parent(tag):
        parents = tag.parents
        for item in parents:
            if item is None:
                return 1
            if item.name == "p" or item.name == "span":
                return 0
        return 1

    def crawl(self):
        pass

    @staticmethod
    def select_url(url):
        sql = Crawler.select_sql % url
        return DBUtil.select_data(sql)

    @staticmethod
    def insert_url(url):
        date = datetime.datetime.now()
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        sql = Crawler.insert_sql % (url, date_str)
        DBUtil.insert_data(sql)

    @staticmethod
    def replace_white_space(src_str):
        if src_str:
            return src_str.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "")
        else:
            return ""

    @staticmethod
    def extract(bs_obj):
        if bs_obj:
            bs_obj.extract()

    @staticmethod
    def extract_all(bs_obj_arr):
        if bs_obj_arr:
            [item.extract() for item in bs_obj_arr]

    @staticmethod
    def reset_image_url(image_url):
        pos = image_url.find("?")
        if pos > 0:
            image_url = image_url[:pos]
        pos = image_url.find("!")
        if pos > 0:
            image_url = image_url[:pos]
        return image_url
