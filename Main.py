# coding=utf-8

from db_util import DBUtil


if __name__ == "__main__":
    sql = "select title from t_article where title like \"%百页%\""
    result = DBUtil.select_data(sql)
    s = "d"

    print(result["title"])
