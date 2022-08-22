"""
    redis分布式锁示例
    模拟30个并发随机向8000和8001发请求
"""
import random
import requests
from threading import Thread


def stock_func():
    url1 = "http://127.0.0.1:8000/v1/stock"
    url2 = "http://127.0.0.1:8001/v1/stock"

    resp = requests.get(url=random.choice([url1, url2])).json()
    print(resp)


t_list = []

for i in range(30):
    t = Thread(target=stock_func)
    t_list.append(t)
    t.start()

for t in t_list:
    t.join()

















