"""
    测试登录功能
"""
import requests


url = "http://127.0.0.1:8000/v1/tokens"
body = {"username": "zhaoliying", "password": "123456"}

response = requests.post(url=url, json=body)
# text属性: 获取响应内容-字符串 str
print(response.text)
# json(): 获取响应内容-Dict
print(response.json())













