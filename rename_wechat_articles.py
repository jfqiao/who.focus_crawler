# coding=utf-8

from db_util import DBUtil
import os

article_dir = "/home/jfqiao/wechat_articles/"


def rename_file():
    sql = "SELECT url from t_article"
    datas = DBUtil.select_datas(sql)
    for item in datas:
        old_file_name = article_dir + item["url"][28:]
        new_file_name = article_dir + item["url"].replace(":", "").replace("/", "")
        os.rename(old_file_name, new_file_name)


if __name__ == "__main__":
    rename_file()