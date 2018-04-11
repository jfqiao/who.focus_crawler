# coding=utf-8

from xi_gua_crawler_xls import XiGuaCrawler
from wechat_crawler import WechatArticleCrawler
import sys
import os
import pexpect
import datetime
import time

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import paramiko
from paramiko import SSHClient
from scp import SCPClient

from website_crawler import chan_pin_jing_li
from website_crawler import chuang_ye_bang
from website_crawler import do_news
from website_crawler import hu_lian_wang_de_yi_xie_shi
from website_crawler import hu_xiu
from website_crawler import hua_er_jie_jian_wen
from website_crawler import ji_ke_wang
from website_crawler import jie_mian
from website_crawler import jing_li_ren_fen_xiang
from website_crawler import ju_shuo_she
from website_crawler import kr
from website_crawler import lie_yun_wang
from website_crawler import mi_ke_wang
from website_crawler import pin_tu
from website_crawler import pin_wan
from website_crawler import tai_mei_ti
from website_crawler import xiao_bai_chuang_ye

from website_crawler.crawler import Crawler

host = "118.190.201.165"

# host = "39.107.69.102"

user = "jfqiao"

password = "jfq19940210"


def wechat_article_crawler():
    sys.setrecursionlimit(100000)
    XiGuaCrawler.xi_gua_crawl()
    WechatArticleCrawler.get_url_and_set(XiGuaCrawler.file_path)
    path_dir, target_dir = get_dir(WechatArticleCrawler.article_dir)
    os.chdir(path_dir)
    os.system("tar -czvf result1.tar.gz \"%s\"" % target_dir)
    src = path_dir + "/result1.tar.gz"
    target = "/home/jfqiao/result/"
    transfer_file(src, target, host, user, password)
    os.system("rm -rf %s/result1.tar.gz" % path_dir)
    send_mail(WechatArticleCrawler.wechat_article_result_path)

# def send_email():
#     mail_host = "smtp.163.com"  # 使用的邮箱的smtp服务器地址，这里是163的smtp地址
#     mail_user = "jfqiao123"  # 用户名
#     mail_pass = "tsi52hc8old"  # 密码
#     # mail_postfix = "163.com"
#
#     sender = 'jfqiao123@163.com'
#     receivers = ['jfqiao.123@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
#
#     # 创建一个带附件的实例
#     message = MIMEMultipart()
#     message['From'] = Header("jfqiao", 'utf-8')
#     message['To'] = Header("jfqiao.123", 'utf-8')
#     subject = 'Python SMTP 邮件测试'
#     message['Subject'] = Header(subject, 'utf-8')
#
#     # 邮件正文内容
#     message.attach(MIMEText('电话是123312313', 'plain', 'utf-8'))
#
#     # 构造附件1，传送当前目录下的 test.txt 文件
#     att1 = MIMEText(open('/Users/jfqiao/Desktop/huxiu_test.html', 'rb').read(), 'base64', 'utf-8')
#     att1["Content-Type"] = 'application/octet-stream'
#     # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
#     att1["Content-Disposition"] = 'attachment; filename="huxiu_test.html"'
#     message.attach(att1)
#
#     # 构造附件2，传送当前目录下的 runoob.txt 文件
#     # att2 = MIMEText(open('runoob.txt', 'rb').read(), 'base64', 'utf-8')
#     # att2["Content-Type"] = 'application/octet-stream'
#     # att2["Content-Disposition"] = 'attachment; filename="runoob.txt"'
#     # message.attach(att2)
#
#     try:
#         smtpObj = smtplib.SMTP()
#         smtpObj.connect(mail_host)
#         smtpObj.login(mail_user, mail_pass)
#         smtpObj.sendmail(sender, receivers, message.as_string())
#         print("邮件发送成功")
#     except smtplib.SMTPException as e:
#         print("Error: 无法发送邮件. ErrMsg: %s" % str(e))


def send_mail(att_path):
    mailto_list = ['459003761@qq.com', "867309733@qq.com", "jfqiao.123@qq.com"]  # 收件人(列表)
    mail_host = "smtp.163.com"  # 使用的邮箱的smtp服务器地址，这里是163的smtp地址
    mail_user = "jfqiao123"  # 用户名
    mail_pass = "tsi52hc8old"  # 密码
    mail_postfix = "163.com"  # 邮箱的后缀，网易就是163.com
    me = "jfqiao"+"<"+mail_user+"@"+mail_postfix+">"
    sub = "最新文章列表"
    content = "最新爬的文章列表。"
    msg = MIMEMultipart()
    msg.attach(MIMEText(content, "plain", "utf-8"))
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(mailto_list)                # 将收件人列表以‘；’分隔
    # 构造附件1，传送文件
    pos = att_path.rfind("/")
    file_name = att_path[pos + 1:]
    att1 = MIMEText(open(att_path, 'rb').read(), 'base64', 'utf-8')

    att1["Content-Type"] = 'application/octet-stream'
    # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    att1["Content-Disposition"] = 'attachment; filename="%s"' % file_name
    msg.attach(att1)
    try:
        # server = smtplib.SMTP()
        # server.connect(mail_host)                            # 连接服务器
        # server.login(mail_user, mail_pass)               # 登录操作
        # server.sendmail(me, mailto_list, msg.as_string())
        # server.close()
        smtp = smtplib.SMTP_SSL(mail_host, 465)
        smtp.ehlo()
        smtp.login(mail_user, mail_pass)
        # server = smtplib.SMTP()
        # server.connect(mail_host)                            # 连接服务器
        # server.login(mail_user, mail_pass)               # 登录操作
        smtp.sendmail(me, mailto_list, msg.as_string())
        smtp.close()
        return True
    except Exception as e:
        print(str(e))
        return False


def website_crawler():
    Crawler.initialize_workbook()
    chan_pin_jing_li.crawl()
    chuang_ye_bang.crawl()
    do_news.crawl()
    # gui_gu_mi_tan.crawl()
    hu_lian_wang_de_yi_xie_shi.crawl()
    hu_xiu.crawl()
    hua_er_jie_jian_wen.crawl()
    ji_ke_wang.crawl()
    jie_mian.crawl()
    jing_li_ren_fen_xiang.crawl()
    ju_shuo_she.crawl()
    # ke_ji_lie.crawl()
    kr.crawl()
    lie_yun_wang.crawl()
    mi_ke_wang.crawl()
    pin_wan.crawl()
    pin_tu.crawl()
    tai_mei_ti.crawl()
    xiao_bai_chuang_ye.crawl()
    Crawler.save_workbook()
    Crawler.is_article_dir_exists = 0   # 设置状态为0，下次启动时重新创建文件夹
    send_mail(Crawler.write_file_path)
    article_path_dir, article_target_dir = get_dir(Crawler.write_article_path)
    os.chdir(article_path_dir)
    os.system("tar -czvf result2.tar.gz %s" % article_target_dir)
    src = article_path_dir + "/result2.tar.gz"
    target = "/home/jfqiao/result/"
    transfer_file(src, target, host, user, password)
    os.system("rm -rf %s/result2.tar.gz" % article_path_dir)
    image_path_dir, image_target_dir = get_dir(Crawler.write_image_path)
    os.chdir(image_path_dir)
    os.system("tar -czvf result3.tar.gz %s" % image_target_dir)
    src = image_path_dir + "/result3.tar.gz"
    transfer_file(src, target, host, user, password)
    os.system("rm -rf %s/result3.tar.gz" % image_path_dir)


def server_deal_with_articles():
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, 22, user, password)
    stdin, stdout, stderr = ssh.exec_command("python /home/jfqiao/project/who.focus_crawler/tar_and_move.py")
    print(stdout.read())
    ssh.close()


def timer():
    time_to_crawl = {0: 0, 9: 1, 11: 0, 13: 0, 14: 0, 17: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0}
    previous = 9
    while 1:
        now = datetime.datetime.now()
        if time_to_crawl.get(now.hour) == 0:
            wechat_article_crawler()
            website_crawler()
            server_deal_with_articles()
            if now.hour == 24 or now.hour == 0:
                time_gap = datetime.timedelta(days=1)
                Crawler.target_date = now - time_gap              # 重置网站爬虫时间
            time_to_crawl[now.hour] = 1
            if previous != -1:
                time_to_crawl[previous] = 0
            previous = now.hour
            time.sleep(2000)  # 预留10分钟用于爬虫时间
        # print(now.second)
        time.sleep(1)

def get_dir(path):
    if path.endswith("/"):
        path = path[:-1]
    pos = path.rfind("/")
    path_dir = path[:pos]
    target_dir = path[pos + 1:]
    return path_dir, target_dir


def transfer_file(src, target, host_para, user_para, password_para):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host_para, 22, user_para, password_para)
    # SCPCLient takes a paramiko transport as its only argument
    scp = SCPClient(ssh.get_transport())
    scp.put(src, target)
    scp.close()
    ssh.close()


if __name__ == "__main__":
    # timer()
    now = datetime.datetime.now()
    time_gap = datetime.timedelta(days=1)
    Crawler.target_date = now - time_gap
    wechat_article_crawler()
    website_crawler()
    server_deal_with_articles()
