import requests
from bs4 import BeautifulSoup
import xlwt
import datetime

import re


# 将cookie字符串转换为字典
cookies_dict = {}

# 直接登录后拿到的cookie, 以后需要模拟登录拿数据
cookies_str = '_chl=key=FromBaidu&word=6KW/55Oc5YWs5LyX5Y+35Yqp5omL; Hm_lvt_72aa476a79cf5b994d99ee60fe6359aa=1519877093,1520314467; LoginTag=a9c2d09d95da4e668a9730d103fa4ff9; _XIGUASTATE=XIGUASTATEID=b9046bc650534e7bb8325da9000c58ce; Hm_lpvt_72aa476a79cf5b994d99ee60fe6359aa=1520314469; ASP.NET_SessionId=n4llk4tgfij3djdbvubjwugm; _XIGUA=UserId=d471a30ba6f3c365&Account=fd0673b157bef6e1f2b65e9f22a7aed8&checksum=4be8ae8c72b3; SaveUserName=18911949659; LV2=1; Big3Biz672571=False; ExploreTags672571=; ShowOneKeyAsyncTip=1; SERVERID=0a1db1b547a47b70726acefc0225fff8|1520314511|1520314468; ShowOneKeyAsyncTip2=1'

enter_url = "http://zs.xiguaji.com/MArticle/Attention"

tag_article_url = "http://zs.xiguaji.com/MArticle/Attention/?tags=%s&position=2"

# 用来获取每一页的URL，有的标签下只有一页，有的标签下有多页。
page_url_format = "http://zs.xiguaji.com/MArticle/Attention/?position=2&dayInterval=1&articleType=-1&tags=%s&onlyTopLine=&page=%d&more=1"

# position 1 表示近24小时

# position 2 表示近12小时

# 西瓜爬文章的逻辑：设置登录cookie，从enter-url进入，然后获取每个分组的消息。首先拿到每个分组的tagID，然后根据tag_article_url请求更多

articles_dir = "/Users/jfqiao/Desktop/xi_gua_articles/"
line_format = "%s,%s,%s,%s,%s,%s"


def set_cookie_dict():
    strs = cookies_str.split(";")
    for string in strs:
        pos = string.index("=")
        key = string[:pos].replace(" ", "")
        value = string[pos + 1:].replace(" ", "")
        cookies_dict[key] = value
    print(cookies_dict)


def xi_gua_crawl():
    set_cookie_dict()
    file_name = articles_dir + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    f = open(file_name + ".csv", "wt")
    set_cookie_dict()
    r = requests.get(enter_url, cookies=cookies_dict)
    serverid = r.cookies.get("SERVERID")
    cookies_dict["SERVERID"] = serverid
    bs_obj = BeautifulSoup(r.content, "lxml")
    tags = bs_obj.find("ul", id="ulMyTagList").findAll("li", attrs={"data-loaded": re.compile("[01]")})
    tags_dict = {}
    for li_tag in tags:
        tag_name = li_tag.get("data-tagname")
        tag_id = li_tag.get("data-tagid")
        tags_dict[tag_name] = tag_id
    keys = tags_dict.keys()
    for key in keys:
        craw_tag(key, tags_dict.get(key), f)
    f.close()
    # write_workbook = xlwt.Workbook(encoding="ascii")
    # write_sheet = write_workbook.add_sheet("articles")
    # f = open(file_name + ".csv", "r")
    # convert_csv_to_xls(f, write_sheet)
    # write_workbook.save(file_name + ".xls")


def convert_csv_to_xls(csv_file, write_sheet):
    line_count = 1
    write_sheet_write(write_sheet, line_count, "标题", "链接", "图片链接", "标签", "来源", "发布时间（相对）", "发布时间（绝对）")
    while 1:
        line = csv_file.readline()[:-2]
        if len(line) == 0:
            break
        strs = line.split(",")
        line_count += 1
        write_sheet_write(write_sheet, line_count, strs[0], strs[1], "", strs[2], strs[3], strs[4], strs[5])


def write_sheet_write(write_sheet, line_count, title, link, image_link, tag, origin, rel_time, standard_time, score):
    write_sheet.write(line_count, 1, title)
    write_sheet.write(line_count, 2, link)
    write_sheet.write(line_count, 3, image_link)
    write_sheet.write(line_count, 4, tag)
    write_sheet.write(line_count, 5, origin)
    write_sheet.write(line_count, 7, rel_time)
    write_sheet.write(line_count, 6, standard_time)


def craw_tag(tag_name, tag_id, f):
    page = 1
    while 1:
        url = page_url_format % (tag_id, page)
        r = requests.get(url, cookies=cookies_dict)
        serverid = r.cookies.get("SERVERID")
        cookies_dict["SERVERID"] = serverid
        if len(r.content) < 100:      # page页面没有了之后返回的长度是24
            break
        bs_obj = BeautifulSoup(r.content, "html.parser")
        article_tags = bs_obj.findAll("tr", attrs={"data-articleid": re.compile(".*")})
        for article_tag in article_tags:
            title_tag = article_tag.find("div", class_="mp-article-title")
            href_tag = title_tag.find("a")
            title = href_tag.get_text().replace("\n", "")
            link = href_tag.get("href")
            source_tag = article_tag.find("div", class_="item-source")
            origin = source_tag.find("div", class_="item-title").get_text()
            rel_time = source_tag.find("div", class_="item-sub-title").get_text()
            standard_time = convert_time_to_standard_time(rel_time)
            f.write(line_format % (title, link, tag_name, origin, rel_time, standard_time))
            f.write("\n")
            f.flush()
        page += 1


def convert_time_to_standard_time(rel_time):
    '''
    将XX小时或分钟前这种相对时间转化为标准时间。yyyy-mm-dd HH:MM:SS
    :param rel_time:
    :return:
    '''
    cur_time = datetime.datetime.now()

    if "小时" in rel_time:
        pos = rel_time.find(" ")
        hours = int(rel_time[:pos])
        time_delta = datetime.timedelta(hours=hours)
    elif "分钟" in rel_time:
        pos = rel_time.find(" ")
        minutes = int(rel_time[:pos])
        time_delta = datetime.timedelta(minutes=minutes)
    else:
        time_delta = datetime.timedelta(seconds=0)
    cur_time -= time_delta
    return cur_time.strftime("%Y-%m-%d %H:00:00")


if __name__ == "__main__":
    xi_gua_crawl()
