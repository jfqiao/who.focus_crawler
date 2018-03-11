# coding=utf-8

from db_util import DBUtil

write_line_format = "%s,%s\n"

colleges = ["哲学院", "经济学院", "法学院", "教育学院", "文学院", "历史学院", "理学院", "工学院", "农学院", "医学院", "管理学院", "艺术学院",
            "其他"]


def write_colleges(f, school_name):
    for college in colleges:
        f.write(write_line_format % (school_name, college))


def select_school():
    sql = "select id, school_name from t_school"
    schools = DBUtil.select_datas(sql)
    return schools


def select_school_college():
    sql = "select DISTINCT(school_id) from t_school_college"
    school_colleges = DBUtil.select_datas(sql)
    return school_colleges


def insert_college_to_school():
    f = open("/Users/jfqiao/Desktop/school_colleges.csv", "w")
    school_colleges = select_school_college()
    schools = select_school()
    school_colleges_array = []
    for item in school_colleges:
        school_colleges_array.append(item["school_id"])
    for item in schools:
        if item["id"] not in school_colleges_array:
            write_colleges(f, item["school_name"])
    f.close()


if __name__ == "__main__":
    insert_college_to_school()
