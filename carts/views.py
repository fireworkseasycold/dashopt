from django.conf import settings
from django.http import JsonResponse

from goods.models import SKU
from utils.baseview import BaseView
from django.core.cache import caches


CARTS_CACHE = caches["carts"]

#使用django原生实现
class CartsView(BaseView):
    def post(self, request, username):
        """
        添加购物车视图逻辑
        1.获取请求体数据(sku_id、count)
        2.存入redis数据库
          "carts_1": {
              "1": [8,1],
              "2": [7,1]
          }
        3.组织数据返回
        """
        mydata = request.mydata
        myuser = request.myuser

        sku_id = mydata.get("sku_id")
        count = mydata.get("count")

        print(sku_id, type(sku_id))
        print(count, type(count))

        # 获取用户购物车中所有数据(字典)
        # {"1":[8,1], "2":[9,0]}
        carts_dict = self.get_carts_dict(myuser.id)
        if sku_id not in carts_dict:
            carts_dict[sku_id] = [int(count), 1]
        else:
            new_count = carts_dict[sku_id][0] + int(count)
            carts_dict[sku_id][0] = new_count

        # 更新到redis
        key = f"carts_{myuser.id}"
        CARTS_CACHE.set(key, carts_dict)

        result = {
            'code': 200,
            'data': {'carts_count': len(carts_dict)},
            'base_url': settings.PIC_URL
        }
        return JsonResponse(result)

    def get(self, request, username):
        """
        查询购物车视图逻辑
        1.Redis中获取购物车数据
        2.MySQL中获取相关数据
        3.返回响应{"code":200, "data":[{},{},..], "base_url": "xxx}
        """
        myuser = request.myuser
        carts_dict = self.get_carts_dict(myuser.id)
        skus_list = self.get_skus_list(carts_dict)

        result = {
            "code": 200,
            "data": skus_list,
            "base_url": settings.PIC_URL
        }

        return JsonResponse(result)

    def delete(self, request, username):
        """
        删除购物车商品视图逻辑
        1.获取请求体数据(sku_id)
        2.Redis数据中删除该sku_id，并更新
        3.组织数据返回
        """
        # 1.请求体数据
        mydata = request.mydata
        sku_id = mydata.get("sku_id")

        # 2.获取用户购物车数据并删除sku_id商品
        #   carts_dict: {"1":[8,1], "2":[5,0]}
        myuser = request.myuser
        carts_dict = self.get_carts_dict(myuser.id)
        if str(sku_id) not in carts_dict:
            return JsonResponse({"code": 10300, "error": "该商品不存在!"})

        del(carts_dict[str(sku_id)])
        key = f"carts_{myuser.id}"
        CARTS_CACHE.set(key, carts_dict)

        result = {
            "code": 200,
            "data": {"carts_count": len(carts_dict)},
            "base_url": settings.PIC_URL
        }
        return JsonResponse(result)

    def put(self, request, username):
        """
        购物车商品单选和取消单选视图逻辑
        1.获取请求体数据(sku_id state)
        2.获取用户购物车数据,更新并保存到redis
        3.组织数据返回
        """
        mydata = request.mydata
        # carts_dict: {"1":[8,1], "2":[5,0]}
        myuser = request.myuser
        carts_dict = self.get_carts_dict(myuser.id)

        sku_id = mydata.get("sku_id")

        if sku_id:
            if sku_id not in carts_dict:
                return JsonResponse({"code": 10301, "error": "商品不存在!"})

        state = mydata.get("state")

        if state == "select":
            carts_dict[sku_id][1] = 1
        elif state == "unselect":
            carts_dict[sku_id][1] = 0
        elif state == "selectall":
            carts_dict = {k: [v[0], 1] for k, v in carts_dict.items()}
        elif state == "unselectall":
            carts_dict = {k: [v[0], 0] for k, v in carts_dict.items()}
        elif state == "add":
            carts_dict[sku_id][0] += 1
        elif state == "del":
            carts_dict[sku_id][0] -= 1

        key = f"carts_{myuser.id}"
        CARTS_CACHE.set(key, carts_dict)

        # 组织数据返回
        skus_list = self.get_skus_list(carts_dict)
        result = {
            'code': 200,
            'data': skus_list,
            'base_url': settings.PIC_URL
        }

        return JsonResponse(result)

    def get_carts_dict(self, user_id):
        """
        功能函数:获取购物车的所有数据 需要合并（登录和非登录下的购物车）
        :return: {} 或者 {"1":[8,1], "2":[6,0],... ...}  #后面的0/1，为1代表选中状态
        """
        key = f"carts_{user_id}"
        carts_dict = CARTS_CACHE.get(key)
        if not carts_dict:
            return {}

        return carts_dict

    def get_skus_list(self, carts_dict):
        """
        功能函数:获取购物车数据(mysql)
        :param carts_dict: {"1":[8,1], "2":[2,0]}
        :return: skus_list [{8个键值对},...]
        """
        skus_list = []
        for sku_id in carts_dict:
            sku = SKU.objects.get(id=int(sku_id))
            value_query = sku.sale_attr_value.all()
            sku_dict = {
                "id": sku.id,
                "name": sku.name,
                "count": carts_dict[sku_id][0],
                "selected": carts_dict[sku_id][1],
                "default_image_url": str(sku.default_image_url),
                "price": sku.price,
                "sku_sale_attr_name": [i.spu_sale_attr.name for i in value_query],
                "sku_sale_attr_val": [i.name for i in value_query]
            }
            skus_list.append(sku_dict)

        return skus_list

    #后续添加
    def merge_carts(self,uid,carts_data):
        """合并浏览器存的和redis里的购物车
        carts_data为前端浏览器存储的购物车传过来的key
        需要更新小红点，所以返回值为len(carts_dict)"""
        carts_dict=self.get_carts_dict(uid)
        print(f"carts_dict={carts_dict}")
        if not carts_data:
            #用户离线状态下未使用购物车
            return len(carts_dict)

        for c_dic in carts_data:

            sku_id=int(c_dic['id'])
            try:
                sku_data=SKU.objects.get(id=sku_id,is_launched=True)
            except Exception as e:
                continue
            c_count=int(c_dic['count'])

            #判断后端购物车是否有该商品
            if sku_id in carts_dict:
                #后端购物车有该商品
                sku_count=carts_dict[sku_id][0]
                last_count=min(sku_data.stock,max(sku_count,c_count))  #先取两个购物车该商品数目最大值，再和库存取最小值,
                #改写后端数据
                carts_dict[sku_id][0]=last_count
            else:
                #后端购物车没有该商品,将此商品添加入后端购物车
                carts_dict[sku_id]=[min(sku_data.stock,c_count),1]
                # 更新到redis
                key = f"carts_{uid}"
                CARTS_CACHE.set(key, carts_dict)

        return len(carts_dict)










