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
        os.system("mv %s %s" % (old_file_name, new_file_name))


def replace_white_space():
    path = "/home/jfqiao/wechat_articles"
    for root, dirs, files in os.walk(path):
        for name in files:
            if "_abstract" in name:
                f = open(path + name, "r")
                content = ""
                while 1:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    content += line
                f.close()
                content = content.replace("\n", "")
                f = open(path + name, "w")
                f.write(content)
                f.close()


if __name__ == "__main__":
    rename_file()
