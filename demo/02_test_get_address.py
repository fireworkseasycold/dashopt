"""
    测试地址管理-查询地址功能
"""
import requests

url = "http://127.0.0.1:8000/v1/users/zhaoliying/address"
headers = {"authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2NTI3NzcwNTUsInVzZXJuYW1lIjoiemhhb2xpeWluZyJ9.5ookEoL-CyzgBcLRhqEDMgPAD2KI1ttoQ4j7-zoUjX0"}

response = requests.get(url=url, headers=headers).json()
print(response)













