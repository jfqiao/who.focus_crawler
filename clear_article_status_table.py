# coding=utf-8

import datetime
import os
import pexpect

from db_util import DBUtil


class ClearFunction(object):

    """
     对t_article_status表进行更新，按照时间进行删除，可以是给定时间段，也可以给定时间差（以现在的时间为基准）。
     对timestamp进行比较直接用字符串比较即可。
    """

    DATE_FORMAT_STR = "%Y-%m-%d %H:%M:%S"

    article_path = "/home/jfqiao/wechat_articles/"

    image_path = "/data/who_focus/image/"

    @staticmethod
    def get_article_info(date_str):
        """
        查询publish_time在一定的时间之后的文章ID
        :param date_str:  给定的时间字符串，格式为 yyyy-mm-dd HH:MM:SS.
        :return: 返回的结果是一个list，其中每一项都是dict，利用列的名字进行索引即可。
        """
        sql = "SELECT id, url, image_url FROM t_article WHERE publish_time <= \"%s\"" % date_str
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
            file_path = ClearFunction.article_path + item["url"].replace(":", "").replace("/", "")
            os.system("rm -rf \"%s*\"" % file_path)     # 删除文章和摘要
            file_path = ClearFunction.image_path + item["image_url"].replace(":", "").replace("/", "")
            os.system("echo jfq19940210 | sudo -S rm -rf \"%s*\"" % file_path)
            # child = pexpect.spawn("sudo rm -rf \"%s*\"" % file_path)       # 删除图片
            # child.waitnoecho()
            # child.sendline("jfq19940210")
            # child.waitnoecho()
            # child.kill(0)

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
        article_ids = ClearFunction.get_article_info(date_str)
        ClearFunction.clear_articles_with_id(article_ids)

    @staticmethod
    def time_convert(date_str):
        """
        按照将每篇文章保留在页面上10个小时的需求（0点到6点不算在保留时间累积），清理文章。每天需要清理的时间为7点到24点。
        每到整点开始清理。7点到16点清理前一天15点到24点的数据，17点清理当天0点到7点的数据（按照时间清理应该给定7点即可，早于7点均会清理），
        18点到24点清理对应8点到14点上传的数据。
        :param date_str: 当前清理的时间
        :return: 需要清理的文章的时间，早于该时间的文章全部清理。
        """
        date_now = datetime.datetime.strptime(date_str, ClearFunction.DATE_FORMAT_STR)
        if 7 <= date_now.hour <= 16:
            date_now = date_now - datetime.timedelta(hours=16)
        elif 17 <= date_now.hour <= 23:
            date_now = date_now - datetime.timedelta(hours=10)
        else:
            date_now = None
        return date_now


if __name__ == "__main__":
    # 当前清理的时间。每隔一个小时就要清理一次，可以写成定时任务。
    date_str_now = "2017-03-11 7:00:00"
    clear_date_str = ClearFunction.time_convert(date_str_now).strftime(ClearFunction.DATE_FORMAT_STR)
    try:
        ClearFunction.delete_article(date_str_now)
    finally:
        ClearFunction.close_db_conn()
