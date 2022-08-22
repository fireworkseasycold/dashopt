from django.urls import path
from . import views

urlpatterns = [
    # 注册功能: v1/users/register
    path("", views.register),
    # 邮件激活: v1/users/activation
    path("activation", views.active_view),
    # 地址管理[新增和查询]: v1/users/<username>/address
    path("<str:username>/address", views.AddressView.as_view()),
    # 地址管理[删除和修改]: v1/users/<username>/address/<id>
    path("<str:username>/address/<int:id>", views.AddressView.as_view()),
    # 地址管理[设置默认]: v1/users/<username>/address/default
    path("<str:username>/address/default", views.DefaultAddressView.as_view()),
    # 短信验证码[注册功能]: v1/users/sms/code
    path("sms/code", views.sms_view),
    # 微博登录[获取授权码code]: v1/users/weibo/authorization
    path("weibo/authorization", views.OAuthWeiBoUrlView.as_view()),
    # 微博登录[获取授权令牌access_token]: v1/users/weibo/users
    path("weibo/users", views.OAuthWeiBoTokenView.as_view()),
]







