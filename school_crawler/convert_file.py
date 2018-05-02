# coding=utf-8

import mammoth
import xlsx2html
import pyexcel

from xhtml2pdf import pisa

from bs4 import BeautifulSoup

from pdf2image import convert_from_path
import os


class ConvertUtil:

    @staticmethod
    def convert_docx_to_html(doc):
        '''

        :param doc: file-obj
        :return: html value.
        '''
        result = mammoth.convert_to_html(doc)
        html = result.value
        return html

    @staticmethod
    def convert_xlsx_to_html(xlsx_path):
        tmp_path = "/tmp/tmp.html"
        xlsx2html.xlsx2html(xlsx_path, tmp_path)

        f = open(tmp_path, "rt")
        cnt = ""
        while 1:
            line = f.readline()
            if len(line) == 0:
                break
            cnt += line
        # os.system("rm -rf %s" % xlsx_path)
        # os.system("rm -rf %s" % tmp_path)
        return cnt

    @staticmethod
    def convert_xls_to_html(xls_path):
        tmp_path = "/tmp/tmp.xlsx"
        pyexcel.save_book_as(file_name=xls_path, dest_file_name=tmp_path)
        return ConvertUtil.convert_xlsx_to_html(tmp_path)

    @staticmethod
    def get_xls_target_cnt(cnt):
        bs_obj = BeautifulSoup(cnt, "lxml")
        table = bs_obj.find("table")
        return table.__str__()


def convert_html_to_pdf(src_html, output_file_name):
    # open output file for writing (truncated binary)
    result_file = open(output_file_name, "w+b")

    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
        src_html,  # the HTML to convert
        dest=result_file)  # file handle to recieve result
    # close output file
    result_file.close()  # close output file

    # return True on success and False on errors
    return pisa_status.err


def cut_image(image_data, cols, rows):
    first_black = True
    left_bottom = [0, 0]
    right_bottom = [0, 0]
    left_top = [0, 0]
    right_top = [0, 0]
    for x in range(rows):
        for y in range(cols):
            if image_data[x, y] < 200:
                if first_black:
                    left_top[0] = x
                    left_top[1] = y
                    first_black = False
                else:
                    left_bottom[0] = x
                    left_bottom[1] = y

        if not first_black:
            break

    x = rows - 1
    first_black = True
    while x >= 0:
        for y in range(cols):
            if image_data[x, y] < 200:
                if first_black:
                    right_top[0] = x
                    right_top[1] = y
                    first_black = False
                else:
                    right_bottom[0] = x
                    right_bottom[1] = y
        if not first_black:
            break
        x -= 1
    return left_bottom, right_bottom, left_top, right_top


def convert_pdf_to_image(pdf_file_name, output_image_file_name):
    images = convert_from_path(pdf_file_name)
    if len(images) == 0:
        return
    image = images[0]            # get every page of pdf
    image = image.convert("L")   # convert rgb image to gray image,
    img_data = image.load()
    (height, width) = image.size # size is an attribute, not a method to call
    lb, rb, lt, rt = cut_image(img_data, cols=width, rows=height)
    # 3 pixel for border
    # if lt[0] - 3 >= 0:
    #     lt[0] -= 3
    # if lt[1] - 3 >= 0:
    #     lt[1] -= 3
    # if rb[0] + 3 < height:
    #     rb[0] += 3
    # if rb[1] + 3 < width:
    #     rb[1] += 3
    region = (lt[0], lt[1], rb[0], rb[1])
    cropimg = image.crop(region)
    cropimg.save(output_image_file_name)


def convert_html_to_image(html_src, output_image_file_name):
    try:
        output_pdf_file_name = "/tmp/output.pdf"
        convert_html_to_pdf(html_src, output_pdf_file_name)
        convert_pdf_to_image(output_pdf_file_name, output_image_file_name)
        os.system("rm -rf %s" % output_pdf_file_name)
    except:
        return False
    return True


if __name__ == "__main__":
    pass
    # pisa.showLogging()
    # src = convert_table(src)
    # output_file_name = "/Users/jfqiao/Desktop/output.pdf"
    # image = convert_from_path(output_file_name)[0]
    # image = image.convert("L")
    # # image.save("/Users/jfqiao/Desktop/gray_image.jpg")
    # print(image.size)
    # img_data = image.load()
    # (height, width) = image.size
    # lb, rb, lt, rt = cut_image(img_data, cols=width, rows=height)
    # print(lb)
    # print(lt)
    # print(rb)
    # print(rt)
    # region = (lt[0] - 3, lt[1] - 3, rb[0] + 3, rb[1] + 3)
    # cronimg = image.crop(region)
    # cronimg.save("/Users/jfqiao/Desktop/cut_image.jpg")
    # # convert_html_to_pdf(src, output_file_name)




