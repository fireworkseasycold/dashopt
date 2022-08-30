from django.urls import path, re_path
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    # 首页展示: v1/goods/index
    path("index", cache_page(10, cache="goods_index")(views.GoodsIndexView.as_view())),  #cache="goods_index"为settings里的key
    #cache_page 缓存删除原理
    #独立存储
    #如何触发删除？ admin后台

    # 详情页展示: v1/goods/detail/
    path("detail/<int:sku_id>", views.GoodsDetailView.as_view()),

    #以下为个人开发接口
    # 详情页选择商品规格sku
    #/v1/goods/sku?1=3&2=2&spuid=1  #key是销售属性id，值是销售属性值id
    path("sku", views.GoodschooseskuView.as_view()),

    # 商品品类页
    # re_path(r'^/catalogs/(?P<catalog_id>\d+)', views.GoodsListView.as_view()),  #这个有误
    path('catalogs/<int:catalog_id>', views.GoodsListView.as_view()),

]









