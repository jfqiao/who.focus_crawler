# coding=utf-8

import datetime
import os
import sys

from db_util import DBUtil


class ClearFunction(object):

    """
    说明：清理文章功能。
    过程：
        一、根据t_article表中的publish_time判断，在给定时间之前的文章全部要被删除
        二、删除的方法是清空t_article_status表以及t_article表，但是不删除文章对应的文件以及图片
        三、清理完后，复制在t_article_status表中依然存在的文章到临时文件夹，
        四、删除文章文件夹以及图片文件夹中所有的文件，将临时文件夹中的文件移动到相应的文件夹下。
    代码操作：
    1 在shell下运行清除状态表
    2 在shell下移动文件到临时的文件夹下
    3 删除现有文章以及图片所有文件
    4 复制文本、图片到相应的文件夹中
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
        delete_article = "DELETE FROM t_article WHERE id = %s"
        for item in article_ids:
            sql = sql_format % item["id"]
            DBUtil.update_data(sql)
            DBUtil.update_data(delete_article % item["id"])
            # 不删除文章，用另外一种方式处理。
            # file_path = ClearFunction.article_path + item["url"].replace(":", "").replace("/", "")
            # os.system("rm -rf \"%s\"" % file_path)     # 删除文章
            # os.system("rm -rf \"%s_abstract\"" % file_path)
            # file_path = ClearFunction.image_path + item["image_url"].replace(":", "").replace("/", "")
            # os.system("echo jfq19940210 | sudo -S rm -rf \"%s\"" % file_path)
            # os.system("echo jfq19940210 | sudo -S rm -rf \"%s.txt\"" % file_path)
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


def move_article_and_image():
    article_id_sql = "SELECT DISTINCT article_id from t_article_status"
    result = DBUtil.select_datas(article_id_sql)
    image_path = "/data/who_focus/image/"
    article_path = "/home/jfqiao/wechat_articles/"
    for item in result:
        sql = "SELECT url, image_url FROM t_article WHERE id=%s" % item["article_id"]
        article = DBUtil.select_data(sql)
        article_file_name = article["url"].replace("/", "").replace(":", "")
        os.system("cp \"%s\" /home/jfqiao/tmp_article/" % (article_path + article_file_name))
        os.system("cp \"%s\" /home/jfqiao/tmp_article/" % (article_path + article_file_name + "_abstract"))
        if article["image_url"].startswith("https://mmbiz.qpic") or article["image_url"].startswith("http://mmbiz.qpic"):
            continue
        pos = article["image_url"].find("?")
        if pos == -1:
            pos = len(article["image_url"])
        image_file_name = article["image_url"][:pos].replace(":", "").replace("/", "")
        os.system("cp \"%s\" /home/jfqiao/tmp_image/" % (image_path + image_file_name))
        os.system("cp \"%s\" /home/jfqiao/tmp_image/" % (image_path + image_file_name + ".txt"))


if __name__ == "__main__":
    # 当前清理的时间。每隔一个小时就要清理一次，可以写成定时任务。
    paras = sys.argv[1]
    if paras == "database":
        date_str_now = sys.argv[2]
        clear_date_str = ClearFunction.time_convert(date_str_now).strftime(ClearFunction.DATE_FORMAT_STR)
        try:
            ClearFunction.delete_article(date_str_now)
        finally:
            ClearFunction.close_db_conn()
    else:
        move_article_and_image()
