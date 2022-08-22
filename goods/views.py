from django.conf import settings
from django.http import JsonResponse
from django.views import View

from goods.models import Catalog, SPU, SKU, SKUImage, SPUSaleAttr, SaleAttrValue, SKUSpecValue

from utils.cache_dec import cache_check


class GoodsIndexView(View):
    def get(self, request):
        """
        首页展示的视图逻辑
        {"code":200, "data":[], "base_url":""}
        """
        print('----数据来自于MySQL数据库----')

        all_catalog = Catalog.objects.all()
        data = []
        for one_catalog in all_catalog:
            # 搞定三个键值对
            one_catalog_dict = {}
            one_catalog_dict["catalog_id"] = one_catalog.id
            one_catalog_dict["catalog_name"] = one_catalog.name
            one_catalog_dict["sku"] = []

            # Catalog -->  SPU  -->  SKU
            spu_ids = SPU.objects.filter(catalog=one_catalog).values("id")
            sku_query = SKU.objects.filter(spu__in=spu_ids)[:3]  #具体参看django的查询器查询谓词
            sku_query = SKU.objects.filter(spu__in=spu_ids,is_launched=True)[:3]  #具体参看django的查询器查询谓词
            # print(sku_query)
            # 处理每个类别下的3个sku
            for sku in sku_query:
                sku_dict = {
                    "skuid": sku.id,
                    "caption": sku.caption,
                    "name": sku.name,
                    # "price": sku.price,使用str来防止python版本等导致的一些问题
                    "price": str(sku.price),
                    # sku.default_image_url是个django的imagefield object 必须str(字段)来返回该字段的值
                    "image": str(sku.default_image_url)
                }
                one_catalog_dict["sku"].append(sku_dict)

            data.append(one_catalog_dict)

        # 组织数据返回
        result = {
            "code": 200,
            "data": data,
            "base_url": settings.PIC_URL
        }
        return JsonResponse(result)


class GoodsDetailView(View):
    @cache_check(key_prefix="gd", key_param="sku_id", cache="goods_detail", expire=60) #key='gd%s'%(sku_id)
    def get(self, request, sku_id):
        """
        详情页展示视图逻辑
        {"code":200, "data":{}, "base_url":"xxx"}
        """
        print('~~~data from mysql, yeah~~~')

        try:
            sku_item = SKU.objects.get(id=sku_id, is_launched=True)
        except Exception as e:
            return JsonResponse({"code": 10200, "error": "该商品不存在"})

        data = {}
        # 类1:类别id 类别name(ER图) SKU->SPU->Catalog
        sku_catalog = sku_item.spu.catalog
        data["catalog_id"] = sku_catalog.id
        data["catalog_name"] = sku_catalog.name

        # 类2：SKU
        data["name"] = sku_item.name
        data["caption"] = sku_item.caption
        data["price"] = sku_item.price
        data["image"] = str(sku_item.default_image_url)
        data["spu"] = sku_item.spu.id

        # 类3：详情图片
        img_query = SKUImage.objects.filter(sku=sku_item)
        # 补充，需要将goods_sku_image里添加对应的1 2 3.jpeg,这时需要str(Imagefield)否则TypeError: Object of type 'ImageFieldFile' is not JSON serializable
        data["detail_image"] = str(img_query[0].image if img_query else "")

        # 类4：销售属性
        sale_query = SPUSaleAttr.objects.filter(spu=sku_item.spu)
        data["sku_sale_attr_id"] = [i.id for i in sale_query]
        data["sku_sale_attr_names"] = [i.name for i in sale_query]

        # 类5：销售属性值
        value_query = sku_item.sale_attr_value.all()
        data["sku_sale_attr_val_id"] = [i.id for i in value_query]
        data["sku_sale_attr_val_names"] = [i.name for i in value_query]

        # 销售属性和销售属性值的对应关系
        """
        "sku_all_sale_attr_vals_id": {
            "7": [11,12],
            "8": [13]
        },
        "sku_all_sale_attr_vals_name": {
            "7": ["18寸","19寸"],
            "8": ["蓝色"]
        },
        """
        sku_all_sale_attr_vals_id = {}
        sku_all_sale_attr_vals_name = {}
        attr_id_list = [i.id for i in sale_query]
        for attr_id in attr_id_list:
            item_query = SaleAttrValue.objects.filter(spu_sale_attr=attr_id)
            sku_all_sale_attr_vals_id[attr_id] = [i.id for i in item_query]
            sku_all_sale_attr_vals_name[attr_id] = [i.name for i in item_query]

        data["sku_all_sale_attr_vals_id"] = sku_all_sale_attr_vals_id
        data["sku_all_sale_attr_vals_name"] = sku_all_sale_attr_vals_name

        # 类6和类7：规格属性名和规格属性值
        """
        "spec": {
            "批次": "2000",
            "数量": "2000",
            "年份": "2000"
        }
        """
        spec = {}
        spec_value_query = SKUSpecValue.objects.filter(sku=sku_item)
        for spec_value in spec_value_query:
            key = spec_value.spu_spec.name
            value = spec_value.name
            spec[key] = value

        data["spec"] = spec
        return JsonResponse({"code": 200, "data": data, "base_url": settings.PIC_URL})

#
# def GoodschooseskuView(View):
#     """
#     前端传过来的数据例如{"1":1,"2":2,"spuid":1}
#     返回对应的图片
#     """
#     def get(request,skuid)
#
#     return None