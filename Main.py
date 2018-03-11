# coding=utf-8

from db_util import DBUtil
import os


if __name__ == "__main__":
    path = "/Users/jfqiao/Desktop/wechat_articles_dir/03_11/"
    sql = "select * from t_article_url where id > 1920"
    results = DBUtil.select_datas(sql)
    for item in results:
        if os.path.exists(path + item["url"][28:]):
            if not os.path.exists(path + item["url"][28:] + "_abstract"):
                print("abstract not exists. %s" % item["id"])
        else:
            print("file not exist %s" % item["id"])
    DBUtil.close_conn()
