from django.urls import path
from . import views

urlpatterns = [
    # 确认订单页: v1/orders/username/advance  +？settlement_type=0/1
    path("<str:username>/advance", views.AdvanceView.as_view()),
    # 生成订单: v1/orders/username
    path("<str:username>", views.OrderInfoView.as_view()),
]













