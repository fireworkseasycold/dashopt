import json

from django.conf import settings
from django.core.paginator import Paginator
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
            #sku_query = SKU.objects.filter(spu__in=spu_ids)[:3]  #具体参看django的查询器查询谓词
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
        # print(result)

        """
        {'code': 200, 'data': [{'catalog_id': 1, 'catalog_name': '手提包', 'sku': [{'skuid': 1, 'caption': '蓝色小尺寸', 'name': '安踏A蓝色小尺寸', 'price': '88.00', 'image': 'sku/1_CWVre0U.png'}, {'skuid': 2, 'caption': '灰色
大尺寸', 'name': '安踏A灰色大尺寸', 'price': '139.00', 'image': 'sku/2_viqhhBm.png'}, {'skuid': 3, 'caption': '蓝色小尺寸', 'name': '安踏B蓝色小尺寸', 'price': '167.00', 'image': 'sku/3_1Dc1Us9.png'}]}], 'base_url': 'ht
tp://127.0.0.1:8008/media/'}
        """
        return JsonResponse(result)


class GoodsDetailView(View):
    @cache_check(key_prefix="gd", key_param="sku_id", cache="goods_detail", expire=60) #key='gd%s'%(sku_id)
    def get(self, request, sku_id):
        """
        详情页展示视图逻辑
        {"code":200, "data":{}, "base_url":"xxx"}
        """
        print('~~~data from mysql, yeah~~~')
        # print(f"详情页请求的skuid={sku_id}")
        try:
            sku_item = SKU.objects.get(id=sku_id, is_launched=True)
        except Exception as e:
            print('没此商品')
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
        print("成功，返回商品sku数据")
        return JsonResponse({"code": 200, "data": data, "base_url": settings.PIC_URL})
"""
{
    "code": 200,
    "data": {
        "catalog_id": 1,
        "catalog_name": "手提包",
        "name": "安踏A蓝色小尺寸",
        "caption": "蓝色小尺寸",
        "price": "88.00",
        "image": "sku/1_CWVre0U.png",
        "spu": 1,
        "detail_image": "sku_images/1.png",
        "sku_sale_attr_id": [
            1,
            2
        ],
        "sku_sale_attr_names": [
            "安踏A/尺寸",
            "安踏A/颜色"
        ],
        "sku_sale_attr_val_id": [
            1,
            2
        ],
        "sku_sale_attr_val_names": [
            "15寸",
            "蓝色"
        ],
        "sku_all_sale_attr_vals_id": {
            "1": [
                1,
                3
            ],
            "2": [
                2,
                4
            ]
        },
        "sku_all_sale_attr_vals_name": {
            "1": [
                "15寸",
                "18寸"
            ],
            "2": [
                "蓝色",
                "灰色"
            ]
        },
        "spec": {}
    },
    "base_url": "http://127.0.0.1:8000/media/"
}
"""


class GoodschooseskuView(View):
    """

    会传入该 sku 所属的 spu 的 id，通过 spu_id 可获取到 spu 下的 sku 列表，之后通过销售属性值进行 sku 筛选，将筛选的 sku id 返回给前端
    前端传过来的数据例如{"1":1,"2":2,"spuid":1}  #属性id(尺寸):销售属性值id,属性id(颜色):销售属性值id，idspuid:spuid；get方法发送查询字符串
    返回对应的图片

    """
    def get(self, request):
        # data = json.loads(request.body)  #解码为python对象
        #ajax为get方法带参数，发送查询字符串
        # print(request.GET)
        # print(f"data:{request.body}")
        data=request.GET
        print(data)
        # < QueryDict: {'1': ['3'], '2': ['2'], 'spuid': ['1']} >  #SPU销售属性id:销售属性值id列表
        #sku_sale_attr_id：
        # 将前端传来的销售属性值id放入列表
        sku_vals = []   #这是前端来的销售属性值的id存放的列表
        result = {}
        for k in data:
            if 'spuid' != k:
                sku_vals.append(data[k])
        print(f"前端传递的销售属性值id列表：{sku_vals}")  #把这个里面的销售属性值id和SaleAttrValue里的比对
        sku_list = SKU.objects.filter(spu=data['spuid'])  #获取spuid对应的sku商品数据

        for sku in sku_list:
            sku_details = dict()
            sku_details['sku_id'] = sku.id
            # 获取对应的sku销售属性值id
            sale_attrs_val_query_lists = SaleAttrValue.objects.filter(sku=sku.id)  #多对多反向查询
            # SKU.objects.filter(sale_attr_value=SaleAttrValue)
            #SKU表里有个sale_attr_value字段是外键指向SaleAttrValu
            #SaleAttrValue里有个外键，指向SPUSaleAttr
            #SPUSaleAttr里有个外键，指向SKU
            # print("销售属性值查询列表：",sale_attrs_val_query_lists)
            sale_attr_val_id = []  #销售属性值对应id组成的列表

            for sale_attrs_val in sale_attrs_val_query_lists:
                sale_attr_val_id.append(str(sale_attrs_val.id))
                print(sale_attrs_val.name)
            # print(f"对比{sku_vals}和{sale_attr_val_id}")

            if sku_vals == sale_attr_val_id:
                result = {"code": 200, "data": sku_details }
        if len(result) == 0:
            result = {"code": 10050, "error": "没有这个样式"}
        return JsonResponse(result)


class GoodsListView(View):
    def get(self, request,catalog_id):  #url传参catalog_id
        """
        首页品类的视图逻辑
        {"code":200, "data":[], "base_url":""}
        """
        # print('----数据来自于MySQL数据库(品类）----')
        # print(f"前端传过来的品类id是:{catalog_id}")

        page = int(request.GET.get('page'))  #前端要求的页 查询字符串
        try:
            one_catalog = Catalog.objects.get(pk=catalog_id)
        except Exception as e:
            print('没此品类')
            return JsonResponse({"code": 10100, "error": "没有该品类"})

        data = []

        # one_catalog_dict = {}
        # one_catalog_dict["catalog_id"] = one_catalog.id
        # one_catalog_dict["catalog_name"] = one_catalog.name
        # one_catalog_dict["sku"] = []

        # Catalog -->  SPU  -->  SKU
        spu_ids = SPU.objects.filter(catalog=one_catalog).values("id")
        # sku_query = SKU.objects.filter(spu__in=spu_ids)[:3]  # 具体参看django的查询器查询谓词
        #sku_query = SKU.objects.filter(spu__in=spu_ids, is_launched=True)[:3]  # 具体参看django的查询器查询谓词
        #sku_query = SKU.objects.filter(spu__in=spu_ids, is_launched=True)[:3]  # 具体参看django的查询器查询谓词
        #上面切出三个数据是因为示例用，实际使用分页
        sku_query = SKU.objects.filter(spu__in=spu_ids, is_launched=True)
        # print(sku_query)
        # 分页
        pagesize = 3  # 设定的每页数据条数，可以后端设置或者前端传递
        paginator = Paginator(sku_query, pagesize)  # 使用分页器分页，每页pagesize
        total = paginator.num_pages  # 总页数 传给前端
        total_data = paginator.count  # 数据条数
        pa={

        }
        sku_query_eachpage = paginator.page(page)  # 根据前端的页数选择每页对应的返回结果
        # Object of type 'sku_query_eachpage' is not JSON serializable解决方法即page对象无法转换为json格式，在用orm的时候可以通过serializers.serialize(‘json’, queryset)来转换为对应的json，不过原生的就不行，因为page对象json无法识别。一开始我的想法是自定义一个json对象，然后作为cls参数传入来识别，后面发现应该是想麻烦了，直接将page对象转为list对象即可，代码修改如下即可：
        # sku_query_p=json.dumps(list(sku_query_eachpage))
        # print(f"sku_query_p:{sku_query_p}")

        # 处理每个类别下的sku 这里只有三个
        for sku in sku_query_eachpage:
            sku_dict = {
                "skuid": sku.id,
                "caption": sku.caption,
                "name": sku.name,
                # "price": sku.price,使用str来防止python版本等导致的一些问题
                "price": str(sku.price),
                # sku.default_image_url是个django的imagefield object 必须str(字段)来返回该字段的值
                "image": str(sku.default_image_url)
            }
            # one_catalog_dict["sku"].append(sku_dict)
            data.append(sku_dict)


        # data.append(one_catalog_dict)

        # 组织数据返回
        result = {
            "code": 200,
            "data": data,
            "paginator": [total,pagesize],
            "base_url": settings.PIC_URL
        }

        # print(result)
        return JsonResponse(result)
