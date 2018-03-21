import pymysql
import logging


class DBUtil(object):

    con = None

    @staticmethod
    def get_conn():
        if DBUtil.con:
            return DBUtil.con
        # 配置MySQL, 返回MySQL connection, 这是针对公司的MySQL数据库设置的。
        con = pymysql.connect(host='localhost',
                              port=3306,
                              user='root',
                              password='qwerty123',
                              db='db_WhoFocus',
                              charset='utf8',
                              cursorclass=pymysql.cursors.DictCursor)
        return con

    @staticmethod
    def insert_data(sql):
        # 插入数据与更新数据都是同一个函数
        connection = DBUtil.get_conn()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()
                cursor.close()
        except BaseException as e:
            # 不知道对应MySQL的异常类型
            logging.error("Insert data error. SQL = " + sql + " ErrorMsg: %s" % str(e))
            raise BaseException()

    @staticmethod
    def select_data(sql):
        # fetchone()返回的是一个字典, 键为列的列名, 值为该列的值,
        # 如果select的值不存在,返回空字典
        # fetchone()返回的是一个字典, 键为表的列名, 值为该列的值,
        # 如果select的值不存在,返回空字典， 数据量仅返回一条
        connection = DBUtil.get_conn()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                connection.commit()
                cursor.close()
                return result
        except BaseException as e:
            logging.error("Query data error. SQL = " + sql)
            raise BaseException()

    @staticmethod
    def close_conn():
        if DBUtil.con:
            try:
                DBUtil.con.close()
            except BaseException as e:
                logging.error("Close SQL connection error. ErrorMsg: %s" % str(e))

    @staticmethod
    def select_then_insert(select_sql, insert_sql):
        """
        很多数据库插入先要进行查询操作,如果不在数据库中,则插入数据
        :param select_sql:
        :param insert_sql:
        :return:
        """
        result = DBUtil.select_data(sql=select_sql)
        if not result:
            DBUtil.insert_data(insert_sql)

    @staticmethod
    def select_datas(sql):
        """
        数据库查询数据，数据量大于一条。
        :param sql:  查询语句
        :return: 返回查询结果。
        """
        connection = DBUtil.get_conn()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                connection.commit()
                cursor.close()
                return result
        except BaseException as e:
            logging.error("Query data error. SQL = " + sql)
            raise BaseException()

    @staticmethod
    def update_data(sql):
        """
        根据sql语句,更新数据库.
        :param sql:
        :return:
        """
        connection = DBUtil.get_conn()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()
                cursor.close()
        except:
            logging.error("Query data error. SQL = " + sql)
            raise BaseException()
