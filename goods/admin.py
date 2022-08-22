from django.contrib import admin
from goods.models import SKU, SPU,SPUSpec,SKUImage,SaleAttrValue,SKUSpecValue,SPUSaleAttr,Brand,Catalog
from django.core.cache import caches


INDEX_CACHE = caches["goods_index"]
DETAIL_CACHE = caches["goods_detail"]


@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):  #这是服务端的缓存，怎么删的方法，在admin里调用源码save_model和delete_model
    def save_model(self, request, obj, form, change):
        # 1.执行父类的方法(更新MySQL数据)
        super().save_model(request, obj, form, change)
        # 2.清除首页的缓存(更新Redis数据-清库)
        INDEX_CACHE.clear()
        print("更新数据时，首页缓存清除~~~")
        # 3.清除详情页的缓存(删除对应的key)
        # obj参数:mysql表中的数据对象
        key = "gd%s" % obj.id
        DETAIL_CACHE.delete(key)
        print("更新数据时，详情页缓存清除~~~")


admin.site.register(Brand)  #后面可以自行在此实现分页
admin.site.register(Catalog)
admin.site.register(SPU)
admin.site.register(SPUSpec)
admin.site.register(SPUSaleAttr)
admin.site.register(SKUSpecValue)
admin.site.register(SKUImage)
admin.site.register(SaleAttrValue)


