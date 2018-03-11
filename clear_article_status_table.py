# coding=utf-8

import datetime

from db_util import DBUtil


class ClearFunction(object):

    """
     对t_article_status表进行更新，按照时间进行删除，可以是给定时间段，也可以给定时间差（以现在的时间为基准）。
     对timestamp进行比较直接用字符串比较即可。
    """

    DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def get_article_id(date_str):
        """
        查询publish_time在一定的时间之后的文章ID
        :param date_str:  给定的时间字符串，格式为 yyyy-mm-dd HH:MM:SS.
        :return: 返回的结果是一个list，其中每一项都是dict，利用列的名字进行索引即可。
        """
        sql = "SELECT id FROM t_article WHERE publish_time < \"%s\"" % date_str
        result = DBUtil.select_datas(sql)
        return result

    @staticmethod
    def clear_articles_with_id(article_ids):
        """
        通过文章的ID删除在t_article_status表中的记录。
        :param article_ids: list，每一项都是dict，通过id索引。
        :return:
        """
        sql_format = "DELETE FROM t_article_status WHERE article_id = %s"
        for item in article_ids:
            sql = sql_format % item["id"]
            DBUtil.update_data(sql)

    @staticmethod
    def close_db_conn():
        DBUtil.close_conn()

    @staticmethod
    def delete_article(date_str=None):
        """
        删除在当前时间两天前的文章。
        :return:
        """
        if date_str is None:
            date_str = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime(ClearFunction.DATE_FORMAT_STR)
        article_ids = ClearFunction.get_article_id(date_str)
        ClearFunction.clear_articles_with_id(article_ids)


if __name__ == "__main__":
    date_str_now = "2017-03-11 12:00:00"
    try:
        ClearFunction.delete_article(date_str_now)
    finally:
        ClearFunction.close_db_conn()
