"""
    权限校验基类:校验用户登录状态
"""
import json

import jwt

from django.conf import settings
from django.http import JsonResponse
from django.views import View
from user.models import UserProfile


class BaseView(View):
    def dispatch(self, request, *args, **kwargs):
        """
        #重写分发方法
        #所有对应该视图类的请求，优先走该方法
        #集中检查登录状态 对应原来的装饰器logging_check
        #集中处理参数，来给视图类其他函数 """
        token = request.META.get("HTTP_AUTHORIZATION")

        try:
            payload = jwt.decode(token, settings.JWT_TOKEN_KEY, algorithms="HS256")
        except Exception as e:
            return JsonResponse({"code": 403, "error": "请登录"})

        # 给request对象增加myuser属性
        username = payload.get("username")
        user = UserProfile.objects.get(username=username)
        request.myuser = user

        # 给request对象增加mydata属性(请求体的数据)，取代每个函数里写json.loads(request.body)
        if request.body:
            request.mydata = json.loads(request.body)   #反序列化，将str（比如字符串）类型的数据转成dict

        return super().dispatch(request, *args, **kwargs)














