# coding=utf-8

from website_crawler.society_website import da_gong_she_ping
from website_crawler.society_website import huan_qiu_wang
from website_crawler.society_website import nan_fang_zhou_mo
from website_crawler.society_website import ren_min_wang
from website_crawler.society_website import xin_jing_bao
from website_crawler.society_website import zaker
from website_crawler.society_website import zhong_guo_jing_ji_wang
from website_crawler.crawler import Crawler


def crawl():
    # Crawler.initialize_workbook()
    da_gong_she_ping.crawl()
    huan_qiu_wang.crawl()
    nan_fang_zhou_mo.crawl()
    ren_min_wang.crawl()
    xin_jing_bao.crawl()
    zhong_guo_jing_ji_wang.crawl()
    zaker.crawl()
    # Crawler.save_workbook()


if __name__ == "__main__":
    crawl()
