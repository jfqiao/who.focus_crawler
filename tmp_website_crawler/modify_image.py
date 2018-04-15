# coding=utf-8

from db_util import DBUtil
import requests

from tmp_website_crawler import do_news
from tmp_website_crawler import jie_mian
from tmp_website_crawler import manager_share
from tmp_website_crawler import pin_wan
from tmp_website_crawler import yi_xie_shi
from website_crawler.crawler import Crawler


def reset_image_url():
    f = open("/home/jfqiao/result_2018-03-21_22-37.csv", "r")
    select_sql_format = "SELECT id FROM t_article WHERE url = \"%s\""
    insert_sql_format = "UPDATE t_article SET image_url = \"%s\" WHERE id = %s"
    while 1:
        line = f.readline()
        if len(line) == 0:
            break
        strs = line.replace("\n", "").split(",")
        select_sql = select_sql_format % strs[0]
        select_result = DBUtil.select_data(select_sql)
        if select_result:
            insert_sql = insert_sql_format % (strs[1], select_result["id"])
            DBUtil.insert_data(insert_sql)
    f.close()


def crawl_image():
    f = open("/Users/jfqiao/Desktop/write_aritlce_dirs/result_2018-03-21_22-37.csv", "r")
    image_dir = "/Users/jfqiao/Desktop/image/"
    f.readline()
    cnt = 1
    while 1:
        line = f.readline()
        if len(line) == 0:
            break
        strs = line.replace("\n", "").split(",")
        src = strs[1].replace(":", "").replace("/", "")
        pos = src.find("?")
        if pos < 0:
            src = src[:pos]
        resp = requests.get(strs[1])
        f_img = open(image_dir + src, "wb")
        f_img.write(resp.content)
        f_img.close()
        print(cnt)
        cnt += 1
    f.close()


if __name__ == "__main__":
    Crawler.initialize_workbook()
    do_news.crawl()
    jie_mian.crawl()
    manager_share.crawl()
    pin_wan.crawl()
    yi_xie_shi.crawl()
    Crawler.save_workbook()