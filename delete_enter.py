import os

path = "/Users/jfqiao/Desktop/wechat_articles_dir/03_08/"


def delete_enter_in_file():
    for root, dirs, file_names in os.walk(path):
        for file_name in file_names:
            if "abstract" in file_name:
                f = open(path + file_name, "r")
                line = ""
                while 1:
                    tmp_line = f.readline()
                    if len(tmp_line) == 0:
                        f.close()
                        break
                    line += tmp_line
                line = line.replace("\n", "").replace("\r", "")
                f = open(path + file_name, "w")
                f.write(line)
                f.close()


if __name__ == "__main__":
    delete_enter_in_file()
