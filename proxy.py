import requests
import time

request_url = "http://tvp.daxiangdaili.com/ip?tid=555876540010987&num=1"
test_url = "http://httpbin.org/get?show_env=1"


def get_proxy():
    count = 0
    while 1:
        count += 1
        r = requests.get(url=request_url)
        ip = r.content.decode("utf-8")
        if test_proxy(ip):
            return {"http": ip}
        time.sleep(1)
        if count > 1000:
            raise BaseException()


def test_proxy(ip):
    proxies = {"http": ip}
    try:
     r = requests.get(test_url, proxies=proxies, timeout=2)
    except requests.ConnectTimeout:
        return 0
    except BaseException as e:
        return 0
    return 1
