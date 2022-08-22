from django.urls import path
from . import views

urlpatterns = [
    # 同步通知[GET 无支付结果]: v1/pays/return_url
    path("return_url", views.ReturnUrlView.as_view()),
    # 异步通知[POST 有支付结果 必须公网IP]: v1/pays/notify_url
    path("notify_url", views.NotifyUrlView.as_view()),
]












