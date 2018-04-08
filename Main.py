# coding=utf-8

from website_crawler import chan_pin_jing_li
from website_crawler import chuang_ye_bang
from website_crawler import do_news
from website_crawler import gui_gu_mi_tan
from website_crawler import hu_lian_wang_de_yi_xie_shi
from website_crawler import hu_xiu
from website_crawler import hua_er_jie_jian_wen
from website_crawler import ji_ke_wang
from website_crawler import jie_mian
from website_crawler import jing_li_ren_fen_xiang
from website_crawler import ju_shuo_she
from website_crawler import ke_ji_lie
from website_crawler import kr
from website_crawler import lie_yun_wang
from website_crawler import mi_ke_wang
from website_crawler import pin_tu
from website_crawler import pin_wan
from website_crawler import tai_mei_ti
from website_crawler import xiao_bai_chuang_ye

from website_crawler.crawler import Crawler


if __name__ == "__main__":
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
