"""
    对接容联云API,实现短信发送
"""
import base64
import random
import time
from hashlib import md5

import requests


class ShortMessageAPI:
    def __init__(self, account_sid, auth_token, app_id, template_id):
        """
        :param account_sid: 账户id,控制台获取
        :param auth_token: 授权令牌,控制台获取
        :param app_id: 应用id,控制台获取
        :param template_id: 短信模板id,测试模板为1
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.app_id = app_id
        self.template_id = template_id

    def get_request_url(self):
        """
        accountSid:  控制台获取
        sig：md5(账户ID + 授权令牌 + 时间戳)
            时间戳：yyyymmddHHMMSS
            sig最后处理为大写
        :return: 请求的url地址
        """
        string = self.account_sid + self.auth_token + time.strftime("%Y%m%d%H%M%S")
        # from hashlib import md5
        m = md5()
        m.update(string.encode())
        sig = m.hexdigest().upper()

        return f"https://app.cloopen.com:8883/2013-12-26/Accounts/{self.account_sid}/SMS/TemplateSMS?sig={sig}"

    def get_request_headers(self):
        """
        生成请求头
        auth: base64(账户ID + ":" + 时间戳)
        :return: 请求包头
        """
        string = self.account_sid + ":" + time.strftime("%Y%m%d%H%M%S")
        auth = base64.b64encode(string.encode()).decode()

        headers = {
            "Accept": "application/json;",
            "Content-Type": "application/json;charset=utf-8;",
            # Content-Length:256; requests模块自动处理
            "Authorization": auth
        }

        return headers

    def get_request_body(self, phone_number, sms_code, expire_time):
        """
        请求体
        :return: 请求体
        """
        data = {
            "to": phone_number,
            "appId": self.app_id,
            "templateId": self.template_id,
            # 您的验证码是{1},请于{2}分钟之内输入
            "datas": [sms_code, expire_time]
        }

        return data

    def send_message(self, phone_number, sms_code, expire_time):
        """接口函数"""
        request_url = self.get_request_url()
        request_headers = self.get_request_headers()
        request_body = self.get_request_body(phone_number, sms_code, expire_time)

        html = requests.post(url=request_url, json=request_body, headers=request_headers).json()

        return html


if __name__ == '__main__':
    # sms_config = {
    #     "account_sid": "8a216da87b52cabc017b58abc72701cd",
    #     "auth_token": "5e8e05d59b81465abbd26cf16c7a2374",
    #     "app_id": "8a216da87b52cabc017b58abc81601d3",
    #     "template_id": "1",
    # }
    sms_config = {
        "account_sid": "8aaf0708825efdb2018273b7db40061d",
        "auth_token": "81f6f12beff84d21b5b8c9f5dc62f664",
        "app_id": "8aaf0708825efdb2018273b7dc2b0624",
        "template_id": "1",
    }
    phone_number = "13451728020"
    sms_code = random.randint(100000, 999999)
    expire_time = 5

    smapi = ShortMessageAPI(**sms_config)
    smapi.send_message(phone_number, sms_code, expire_time)
















