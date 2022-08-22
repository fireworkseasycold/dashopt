"""
    装饰器:校验登录状态(token)
"""
import jwt
from django.conf import settings
from django.http import JsonResponse

from user.models import UserProfile


def logging_check(func):
    def wrapper(self, request, *args, **kwargs):
        """
        1.获取token(请求头)
        2.校验token
          2.1 校验失败,返回403状态码给前端
          2.2 校验成功,则执行对应的视图
        """
        # DJANGO会把请求头大写并加上HTTP_前缀
        token = request.META.get("HTTP_AUTHORIZATION")

        try:
            payload = jwt.decode(token, settings.JWT_TOKEN_KEY, algorithms="HS256")
        except Exception as e:
            return JsonResponse({"code": 403, "error": "请登录"})

        # 给request对象增加myuser属性
        username = payload.get("username")
        user = UserProfile.objects.get(username=username)
        request.myuser = user

        return func(self, request, *args, **kwargs)
    return wrapper





















