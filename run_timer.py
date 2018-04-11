# coding = utf-8
import os
import datetime
import time


def timer():
    cmd = "python /home/jfqiao/project/who.focus_crawler/timer_control.py"
    time_to_crawl = {0: 0, 9: 0, 11: 0, 13: 0, 14: 1, 17: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0}
    previous = 14
    while 1:
        now = datetime.datetime.now()
        if time_to_crawl.get(now.hour) == 0:
            os.system(cmd)
            if previous != -1:
                time_to_crawl[previous] = 0
            previous = now.hour
            time.sleep(2000)  # 预留10分钟用于爬虫时间
        # print(now.second)
        time.sleep(1)


if __name__ == "__main__":
    timer()
