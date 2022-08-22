from django.urls import path
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    # 首页展示: v1/goods/index
    path("index", cache_page(300, cache="goods_index")(views.GoodsIndexView.as_view())),  #cache="goods_index"为settings里的key
    #cache_page 缓存删除原理
    #独立存储
    #如何触发删除？ admin后台

    # 详情页展示: v1/goods/detail/
    path("detail/<int:sku_id>", views.GoodsDetailView.as_view()),
    # 详情页选择商品规格sku
    # path("sku", views.GoodschooseskuView.as_view()),
]









