# coding=utf-8

import os
import pexpect


def tar_and_move():
    path = "/home/jfqiao/result/"
    files = os.listdir(path)
    for file in files:
        os.system("tar -xzvf %s" % path + file)
    files = os.listdir(path)
    for file in files:
        file_path = path + file
        if os.path.isdir(file_path):
            if "2018" in file:
                os.system("cd %s" % file_path)
                child = pexpect.spawn("sudo mv %s/* /data/who_focus/images/" % file_path)
                child.sendline("jfq19940210")
                child.close()
            else:
                os.system("mv %s/* /home/jfqiao/wechat_articles/" % file_path)
    os.system("rm -rf /home/jfqiao/result/*")


if __name__ == "__main__":
    tar_and_move()