# coding=utf-8

import xlwt
import xlrd
import random
import datetime
import requests
from website_crawler.crawler import Crawler
from school_crawler import zhong_guo_zheng_fa_da_xue


class Record(object):

    """
    单个记录表示的类。
    每次爬公众号与文章综合在一起，选择1/3的文章，将这1/3的文章平均分配到11所高校，
    每所高校分配到的文章标记为本校热榜状态。
    每所高校每次上传所有爬到的文章，上述选择的文章标记为状态0，其余标记为状态1。
    标记为状态0的文章热度值在280到330中选择随机数，阅读量为热度值的1到3倍（间隔为0.1）
    标记为状态1的文章热度值在50到200中选择随机数，阅读量规则同上。
    """

    min_hot_rate = 50

    max_hot_rate = 200

    min_hot_rate_status = 220

    max_hot_rate_status = 295

    def __init__(self, title, url, image_url, label, origin, publish_time):
        self.title = title
        self.url = url
        self.image_url = image_url
        self.label = label
        self.origin = origin
        self.publish_time = publish_time
        self.read_num = None
        self.status = None
        self.hot_rate = None


class UploadUtil(object):

    school_result_dir = "/Users/jfqiao/Desktop/write_aritlce_dirs/"

    # school_result_dir = "/home/jfqiao/crawler/school_reuslt_dir/"

    schools = ["北京大学", "清华大学", "复旦大学", "浙江大学", "中国人民大学", "中央财经大学", "对外经济贸易大学", "北京师范大学",
               "中国政法大学", "中山大学", "其他高校"]

    @staticmethod
    def parse_xls_file(file_path, result_list, title_list):
        if file_path is None:
            return
        read_book = xlrd.open_workbook(file_path)
        read_table = read_book.sheet_by_index(0)
        rows = read_table.nrows
        for i in range(1, rows):
            title = read_table.cell(i, 0).value
            if title in title_list or len(title) == 0:
                continue
            else:
                title_list.append(title)
            url = read_table.cell(i, 1).value
            image_url = read_table.cell(i, 2).value
            label = read_table.cell(i, 3).value
            origin = read_table.cell(i, 4).value
            publish_time = read_table.cell(i, 5).value
            result_list.append(Record(title=title, url=url, image_url=image_url, label=label, origin=origin,
                                      publish_time=publish_time))

    @staticmethod
    def select_record(result_list):
        """
        从result_list中随机选出 1/3作为标记为0的文章，其余的文章标记为1
        :param result_list: 待选文章列表, 仅记录下标
        :return:
        """
        result_len = len(result_list)
        target_len = int(result_len / 3)
        count_list = []
        count = 0
        while count < target_len:
            i = random.randint(0, result_len - 1)
            if i in count_list:
                continue
            count_list.append(i)
            count += 1
        return count_list

    @staticmethod
    def get_read_num_by_hot_rate(hot_rate):
        rate = random.randint(11, 29)
        read_num = rate * hot_rate / 10
        return int(read_num)

    @staticmethod
    def set_record_info(result_list, school_status_list):
        list_len = len(result_list)
        for i in range(list_len):
            if i in school_status_list:
                result_list[i].status = 0
                result_list[i].hot_rate = random.randint(Record.min_hot_rate_status, Record.max_hot_rate_status)
            else:
                result_list[i].status = 1
                result_list[i].hot_rate = random.randint(Record.min_hot_rate, Record.max_hot_rate)
            result_list[i].read_num = UploadUtil.get_read_num_by_hot_rate(result_list[i].hot_rate)

    @staticmethod
    def generate_school_xls_file(school_result_list, file_name):
        write_book = xlwt.Workbook(encoding="ascii")
        write_sheet = write_book.add_sheet("articles")
        list_len = len(school_result_list)
        UploadUtil.write_sheet_write(write_sheet, 0, "标题", "链接", "图片链接", "标签", "来源", "发布时间", "阅读量",
                                     "阅读状态", "热度值")
        for line in range(list_len):
            record = school_result_list[line]
            UploadUtil.write_sheet_write(write_sheet, line + 1, record.title, record.url, record.image_url, record.label
                                         , record.origin, record.publish_time, record.read_num, record.status
                                         , record.hot_rate)
        write_book.save(UploadUtil.school_result_dir + file_name + ".xls")

    @staticmethod
    def write_sheet_write(write_sheet, line_count, title, url, image_url, label, origin, publish_time,
                          read_num, status, hot_rate):
        write_sheet.write(line_count, 0, title)
        write_sheet.write(line_count, 1, url)
        write_sheet.write(line_count, 2, image_url)
        write_sheet.write(line_count, 3, label)
        write_sheet.write(line_count, 4, origin)
        write_sheet.write(line_count, 5, publish_time)
        write_sheet.write(line_count, 6, read_num)
        write_sheet.write(line_count, 7, status)
        write_sheet.write(line_count, 8, hot_rate)

    @staticmethod
    def parse_and_generate(file_path_wechat, file_path_website):
        result_list = []
        title_list = []
        UploadUtil.parse_xls_file(file_path_wechat, result_list, title_list)
        UploadUtil.parse_xls_file(file_path_website, result_list, title_list)
        random.shuffle(result_list)   # 打乱文章原来的顺序
        # 选择需要标记为0的1/3文章
        count_list = UploadUtil.select_record(result_list)
        count_len = len(count_list)
        # 均分到11所高校
        schools_count_list = []
        for i in range(11):
            schools_count_list_tmp = []
            schools_count_list.append(schools_count_list_tmp)
        for i in range(count_len):
            j = i % 11
            schools_count_list[j].append(count_list[i])
        time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        for i in range(11):
            UploadUtil.set_record_info(result_list, schools_count_list[i])
            UploadUtil.generate_school_xls_file(result_list, UploadUtil.schools[i] + "_" + time_str)
            UploadUtil.post_file_to_server(UploadUtil.schools[i] + "_" + time_str, UploadUtil.schools[i])

    @staticmethod
    def post_file_to_server(file_name, school):
        url = "https://www.leftbrain.cc/who.focus_test/uploadSchoolArticles"
        data = {"school": school}
        upload_file_name = "result.xls"
        file_name += ".xls"
        files = {"articleFile": (upload_file_name, open(UploadUtil.school_result_dir + file_name, "rb"))}
        resp = requests.post(url, data=data, files=files)
        print(resp.text)

    @staticmethod
    def generate_target_school_message(xls_path, school):
        result_list = []
        title_list = []
        UploadUtil.parse_xls_file(xls_path, result_list, title_list)
        UploadUtil.set_record_info(result_list, [])
        for item in result_list:
            item.status = 3
        time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        UploadUtil.generate_school_xls_file(result_list, school + "_" + time_str)
        UploadUtil.post_file_to_server(school + "_" + time_str, school)   # 上传学校数据


if __name__ == "__main__":
    school_name = "中国政法大学"
    # zhong_guo_zheng_fa_da_xue.crawl()
    path = "/Users/jfqiao/Desktop/write_aritlce_dirs/result_2018-04-30_11-03.xls"
    UploadUtil.generate_target_school_message(path, school_name)
