# coding=utf-8

from db_util import DBUtil
import random


def set_hot_rate_random():
    select_max_id_sql = "SELECT id FROM t_article ORDER BY id DESC LIMIT 1"
    result = DBUtil.select_data(select_max_id_sql)
    if result is None:
        return
    max_id = int(result["id"])
    sql = "SELECT * FROM t_article WHERE id = %s"
    update_sql_format = "UPDATE t_school_article SET hot_rate = %s WHERE id = %s"
    select_school_articles_format = "SELECT * FROM t_school_article WHERE article_id = %s"
    try:
        for item_id in range(1, max_id + 1):
            select_sql = sql % str(item_id)
            result = DBUtil.select_data(select_sql)
            if result is None:
                continue
            else:
                select_school_articles = select_school_articles_format % item_id
                school_results = DBUtil.select_datas(select_school_articles)
                for school_article in school_results:
                    hot_rate = random.randint(10, 20)
                    update_sql = update_sql_format % (hot_rate, school_article["id"])
                    DBUtil.update_data(update_sql)
    finally:
        DBUtil.close_conn()


if __name__ == "__main__":
    set_hot_rate_random()
