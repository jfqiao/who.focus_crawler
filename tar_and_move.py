# coding=utf-8

import os
import pexpect


def tar_and_move():
    path = "/home/jfqiao/result/"
    files = os.listdir(path)
    os.chdir(path)
    for file in files:
        os.system("tar -xzvf %s" % path + file)
    files = os.listdir(path)
    for file in files:
        file_path = path + file
        if os.path.isdir(file_path):
            os.chdir(file_path)
            if "2018" in file:
                os.system("echo jfq19940210 | sudo -S mv %s/* /data/who_focus/image/" % file_path)
                # child = pexpect.spawn("sudo mv %s/* /data/who_focus/image/" % file_path)
                # child.waitnoecho()
                # child.sendline("jfq19940210")
                # child.waitnoecho()
                # child.kill(0)
            else:
                os.system("mv %s/* /home/jfqiao/wechat_articles/" % file_path)
    os.system("rm -rf /home/jfqiao/result/*")


if __name__ == "__main__":
    tar_and_move()