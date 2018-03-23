# coding=utf-8

from tmp_website_crawler.do_news import DoNewsCrawler
from tmp_website_crawler.jie_mian import  JieMianCrawler
from tmp_website_crawler.manager_share import ManagerShareCrawler
from tmp_website_crawler.pin_wan import PinWanCrawler
from tmp_website_crawler.yi_xie_shi import YiXieShiCrawler
from website_crawler.crawler import Crawler


if __name__ == "__main__":
    Crawler.initialize_workbook()
    dn = DoNewsCrawler()
    dn.crawl()
    jm = JieMianCrawler()
    jm.crawl()
    ms = ManagerShareCrawler()
    ms.crawl()
    pw = PinWanCrawler()
    pw.crawl()
    yxs = YiXieShiCrawler()
    yxs.crawl()
    Crawler.save_workbook()
