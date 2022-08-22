import jwt
import json
import time
import base64
import random
from hashlib import md5

import requests
from django.db import transaction
from django.http import JsonResponse
from django.views import View

from carts.views import CartsView
from user.models import UserProfile, Address, WeiBoProfile
from django.conf import settings
from django.core.cache import caches
from django.core.mail import send_mail

from utils.logging_dec import logging_check
from utils.baseview import BaseView
from utils.smsapi import ShortMessageAPI
from .tasks import async_send_active_email, async_send_message


CODE_CACHE = caches["default"]
SMS_CACHE = caches["sms_code"]


def register(request):
    """
    注册功能的视图逻辑
    1.获取请求体数据
    2.判断用户名是否被占用
      2.1 被占用: 直接返回错误响应
      2.2 未被占用: 存入数据表
    3.签发token
    4.返回正确响应(接口文档)
    """
    data = json.loads(request.body)
    username = data.get("uname")
    password = data.get("password")
    phone = data.get("phone")
    email = data.get("email")
    # 短信验证码
    verify = data.get("verify")

    # 校验短信验证码(是否超过5分钟 和 是否正确)
    key_period = "sms_period_%s" % phone
    redis_code = SMS_CACHE.get(key_period)

    if not redis_code:
        # 超过5分钟
        return JsonResponse({"code": 10111, "error": {"message": "验证码已过期,请重新获取!"}})

    if verify != str(redis_code):
        return JsonResponse({"code": 10112, "error": {"message": "验证码错误,请重新输入!"}})

    old_user = UserProfile.objects.filter(username=username)
    if old_user:
        return JsonResponse({"code": 10100, "error": "用户名已被占用"})
    # 处理密码加密
    m = md5()
    m.update(password.encode())
    pwd_md5 = m.hexdigest()

    # 考虑并发
    # 你:只手遮天 - 率先存入数据表
    # 我:只手遮天 - 异常(用户名unique)
    try:
        user = UserProfile.objects.create(username=username, password=pwd_md5, email=email, phone=phone)
    except Exception as e:
        print("用户存入失败:", e)
        return JsonResponse({"code": 10101, "error": "用户名已被占用"})

    # 签发token
    token = make_token(username)

    ############ 发送激活邮件 ###########
    # 1.生成激活链接
    #   http://127.0.0.1:7000/dadashop/templates/active.html?code=base64.b64encode(b"1016_liying")

    verify_url = get_verify_url(username)

    # 2.Celery异步发送激活邮件
    async_send_active_email.delay(email, verify_url)

    # 组织数据返回
    result = {
        'code': 200,
        'username': username,
        'data': {'token': token},
        'carts_count': len(CartsView().get_carts_dict(user.id))
    }

    return JsonResponse(result)


def login_view(request):
    """
    登录功能视图逻辑
    1.获取请求体数据(API文档)
    2.校验用户名
    3.校验密码
    4.签发token
    5.返回响应(API文档)
    """
    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")

    # 校验用户名
    user_query = UserProfile.objects.filter(username=username)
    if not user_query:
        return JsonResponse({"code": 10102, "error": "用户名错误"})

    # 校验密码
    pwd = user_query[0].password
    m = md5()
    m.update(password.encode())
    pwd_user = m.hexdigest()

    if pwd != pwd_user:
        return JsonResponse({"code": 10103, "error": "密码错误"})

    # 签发token
    token = make_token(username)

    result = {
        'code': 200,
        'username': username,
        'data': {'token': token},
        'carts_count': len(CartsView().get_carts_dict(user_query[0].id)) #redis里的购物车
    }
    try: #因为是附属功能，所以最好try以防止影响主功能
        # 合并购物车
        carts_data=data.get('carts')
        # print(carts_data)
        carts_obj=CartsView()
        carts_len=carts_obj.merge_carts(user_query[0].id,carts_data)  #如果出错可以在这里加断点调试
        # print(carts_len)
        result['carts_count']=carts_len
        # print(carts_len)
    except Exception as e:
        # print(e)
        pass
    return JsonResponse(result)


def active_view(request):
    """
    注册功能邮件激活视图逻辑
    1.获取查询字符串(code)
    2.校验随机数
    3.激活该用户(is_active=True 一查二改三保存)
    4.清除该用户的缓存(CODE_CACHE.delete(key))
    5.组织数据返回(API文档)
    # select * from user_user_profile\G;
    """
    # NzgzN19saW5xaW5neGlh
    code = request.GET.get("code")
    code_string = base64.urlsafe_b64decode(code.encode()).decode()
    code_number, username = code_string.split('_')

    key = "email_active_%s" % username
    redis_number = CODE_CACHE.get(key)

    if str(redis_number) != code_number:
        return JsonResponse({"code": 10104, "error": "邮件激活码错误"})

    # 激活
    try:
        user = UserProfile.objects.get(username=username)
    except Exception as e:
        return JsonResponse({"code": 10105, "error": "该用户不存在"})

    user.is_active = True
    user.save()

    # 清除Redis数据
    CODE_CACHE.delete(key)

    return JsonResponse({"code": 200, "data": "激活成功"})


class AddressView(BaseView):
    # @logging_check
    def get(self, request, username):
        """
        查询地址视图逻辑
        查询组织数据返回:{"code":200, "addresslist":[{},..]}
        """
        all_address = Address.objects.filter(user_profile=request.myuser, is_active=True)

        addresslist = []
        for addr in all_address:
            addr_dict = {
                'id': addr.id,
                'address': addr.address,
                'receiver': addr.receiver,
                'receiver_mobile': addr.receiver_mobile,
                'tag': addr.tag,
                'postcode': addr.postcode,
                'is_default': addr.is_default,
            }
            addresslist.append(addr_dict)

        return JsonResponse({"code": 200, "addresslist": addresslist})

    # @logging_check
    def post(self, request, username):
        """
        新增地址视图逻辑
        1.获取请求体数据
        2.存入数据表(Address)
          2.1 之前无地址,则新增地址并设置为默认
          2.2 之前有地址,则新增
        3.组织数据返回
        """
        data = json.loads(request.body)
        receiver = data.get("receiver")
        receiver_phone = data.get("receiver_phone")
        address = data.get("address")
        postcode = data.get("postcode")
        tag = data.get("tag")

        user = request.myuser
        old_address = Address.objects.filter(user_profile=user, is_active=True)

        is_default = False if old_address else True

        Address.objects.create(
            user_profile=user,
            receiver=receiver,
            address=address,
            postcode=postcode,
            receiver_mobile=receiver_phone,
            tag=tag,
            is_default=is_default
        )

        # 组织数据返回
        return JsonResponse({"code": 200, "data": "新增地址成功!"})

    # @logging_check
    def put(self, request, username, id):
        """
        更新地址视图逻辑
        :param id: 地址id
        1.获取请求体的数据
        2.一查二改三保存
        3.组织数据返回(API文档)
        """
        # 1.获取请求体数据
        data = json.loads(request.body)
        receiver = data.get("receiver")
        receiver_mobile = data.get("receiver_mobile")
        address = data.get("address")
        tag = data.get("tag")

        # 2.ORM更新(一查二改三保存)
        addr_query = Address.objects.filter(user_profile=request.myuser, id=id)
        if not addr_query:
            return JsonResponse({"code": 10109, "error": "没有该地址!"})

        addr = addr_query[0]
        addr.receiver = receiver
        addr.receiver_mobile = receiver_mobile
        addr.address = address
        addr.tag = tag

        addr.save()

        # 3.组织数据返回
        return JsonResponse({"code": 200, "data": "地址修改成功!"})

    # @logging_check
    def delete(self, request, username, id):
        """
        删除地址的视图逻辑
        :param id: 地址id
        1.查询要删除的地址对象
        2.删除(is_active=False 一查二改三保存)
        3.组织数据返回
        """
        try:
            address = Address.objects.get(user_profile=request.myuser, id=id, is_active=True)
        except Exception as e:
            return JsonResponse({"code": 10108, "error": "该地址不存在!"})

        # 一查二改三保存
        address.is_active = False
        address.save()

        return JsonResponse({"code": 200, "data": "删除地址成功!"})


class DefaultAddressView(BaseView):
    # @logging_check
    def post(self, request, username):
        """
        设置默认地址视图逻辑
        1.获取请求体数据(地址id)
        2.将原来默认地址取消默认,将该地址设置为默认(事务)
        3.返回响应(API文档)
        """
        if request.myuser.username != username:
            return JsonResponse({"code": 10107, "error": "违法请求!"})

        data = json.loads(request.body)
        addr_id = data.get("id")
        user = request.myuser
        # 开启事务
        with transaction.atomic():
            # 创建存储点
            sid = transaction.savepoint()
            try:
                # 1.原来默认地址设置为非默认
                old_default = Address.objects.filter(user_profile=user, is_default=True)
                if old_default:
                    old_default[0].is_default = False
                    old_default[0].save()

                # 2.将现地址设置为默认地址
                new_default = Address.objects.get(user_profile=user, id=addr_id)
                new_default.is_default = True
                new_default.save()
            except Exception as e:
                print("设置默认地址异常:", e)
                # 回滚
                transaction.savepoint_rollback(sid)
                return JsonResponse({"code": 10106, "error": "设置默认失败!"})

            # 提交事务
            transaction.savepoint_commit(sid)

        return JsonResponse({"code": 200, "data": "设置默认成功!"})


def sms_view(request):
    """
    发送短信验证码视图逻辑
    1.获取请求体数据(手机号)
    2.发送短信
    """
    data = json.loads(request.body)
    phone_number = data.get("phone")

    # Redis: {"sms_13603263409": 871016}
    key = "sms_%s" % phone_number
    redis_code = SMS_CACHE.get(key)
    if redis_code:
        # 1分钟之内发过
        return JsonResponse({"code": "10110", "error": {"message": "一分钟之内只能发送一次"}})

    # 发送短信
    sms_code = random.randint(100000, 999999)
    expire_time = 5

    # celery异步发送短信
    # async_send_message.delay(phone_number, sms_code, expire_time)
    async_send_message(phone_number, sms_code, expire_time)

    # 存入Redis-1分钟控制发送频率
    SMS_CACHE.set(key, sms_code, 60)

    # 存入Redis-5分钟控制验证码有效期
    key_period = "sms_period_%s" % phone_number
    SMS_CACHE.set(key_period, sms_code, 300)

    return JsonResponse({"code": 200, "data": "发送成功"})


class OAuthWeiBoUrlView(View):
    def get(self, request):
        """
        获取微博授权登录页的视图逻辑
        响应: {"code": 200, "oauth_url": "URL地址"}
        """
        oauth_url = f"https://api.weibo.com/oauth2/authorize?client_id={settings.CLIENT_ID}&redirect_uri={settings.REDIRECT_URI}&response_type=code"

        # 前端:window.location.href=response.oauth_url
        return JsonResponse({"code": 200, "oauth_url": oauth_url})


class OAuthWeiBoTokenView(View):
    def get(self, request):
        """
        获取access_token并绑定注册视图逻辑(接口文档oauth2/access_token)
        1.获取授权码code(查询字符串中)
        2.获取access_token(API文档)
        """
        code = request.GET.get("code")

        url = "https://api.weibo.com/oauth2/access_token"
        data = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.REDIRECT_URI
        }
        html = requests.post(url=url, data=data).json()
        print('-------access_token:', html)
        """
         {
               "access_token": "ACCESS_TOKEN",
               "expires_in": 1234,
               "remind_in": "798114",
               "uid": "12341234"
         }
        """

        # 绑定注册流程
        wuid = html.get("uid")
        access_token = html.get("access_token")

        """
        微博表中查询uid是否存在
        情况1:用户第一次微博登录达达商城,绑定注册[201]
        情况2:用户以前扫码登录过
          2.1 已经和正式用户绑定过[200]
          2.2 在绑定注册页关闭页面[201]
        """
        try:
            weibo_user = WeiBoProfile.objects.get(wuid=wuid)
        except Exception as e:
            # 第一次微博登录
            WeiBoProfile.objects.create(wuid=wuid, access_token=access_token)
            return JsonResponse({"code": 201, "uid": wuid})

        # 判定是否和正式用户绑定过
        user = weibo_user.user_profile
        if user:
            username = user.username
            token = make_token(username)
            return JsonResponse({"code": 200, "username": username, "token": token})
        else:
            # 微博登录过,但是关闭了绑定注册页面
            print("私はあなたを爱してます")
            return JsonResponse({"code": 201, "uid": wuid})

    def post(self, request):
        """
        微博用户和正式用户绑定注册视图逻辑
        1.获取请求体数据
        2.存入用户表(UserProfile)
        3.绑定两个用户(更新微博表外键)
        4.签发token、发送激活邮件
        5.返回响应
          {"code":200, "username":"", "token":""}
          {"code":错误状态码,"error":"错误原因"}
        """
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        phone = data.get("phone")
        uid = data.get("uid")

        # 用户名是否可用
        user = UserProfile.objects.filter(username=username)
        if user:
            return JsonResponse({"code": 10112, "error": "用户名已存在~~"})

        pwd_md5 = md5_string(password)
        # 创建正式用户并执行绑定关系[事务]
        with transaction.atomic():
            sid = transaction.savepoint()
            try:
                user_obj = UserProfile.objects.create(username=username, password=pwd_md5, email=email, phone=phone)
                # 更新外键(一查二改三保存)
                weibo_user = WeiBoProfile.objects.get(wuid=uid)
                weibo_user.user_profile = user_obj
                weibo_user.save()
            except Exception as e:
                print("绑定正式用户失败:", e)
                transaction.savepoint_rollback(sid)
                return JsonResponse({"code": 10113, "error": "数据库错误"})

            # 提交事务
            transaction.savepoint_commit(sid)

        # 发送激活邮件
        verify_url = get_verify_url(username)
        async_send_active_email.delay(email, verify_url)
        # 签发token
        token = make_token(username)

        # 返回响应
        return JsonResponse({"code": 200, "username": username, "token": token})


def make_token(username, expire=86400):
    """
    功能函数：生成token
    :return: token
    """
    payload = {
        "exp": int(time.time()) + expire,
        "username": username
    }
    key = settings.JWT_TOKEN_KEY

    # return jwt.encode(payload, key, algorithm="HS256").decode() #AttributeError: 'str' object has no attribute 'decode'
    return jwt.encode(payload, key, algorithm="HS256")


def send_active_email(email, verify_url):
    """
    功能函数：发送激活邮件
    """
    subject = "达达商城激活邮件"
    html_message = """
    尊敬的用户您好,请点击链接进行激活~~~
    <a href="%s" target="_blank">点击此处</a>
    """ % verify_url

    send_mail(subject=subject,
              message="",
              from_email=settings.EMAIL_HOST_USER,
              recipient_list=[email],
              html_message=html_message
              )


def md5_string(string):
    """
    功能函数: md5加密
    """
    m = md5()
    m.update(string.encode())

    return m.hexdigest()


def get_verify_url(username):
    """
    功能函数: 生成邮件激活链接
    """
    code_number = random.randint(1000, 9999)
    code_string = "%d_%s" % (code_number, username)
    code = base64.urlsafe_b64encode(code_string.encode()).decode()
    verify_url = "http://127.0.0.1:7000/dadashop/templates/active.html?code=" + code
    # 将随机数存入django-redis
    key = "email_active_%s" % username
    CODE_CACHE.set(key, code_number, 86400 * 3)

    return verify_url