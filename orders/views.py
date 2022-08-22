import time
from alipay import AliPay

from django.conf import settings
from django.http import JsonResponse
from django.db import transaction

from carts.views import CartsView, CARTS_CACHE
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from user.models import Address
from utils.baseview import BaseView


class AdvanceView(BaseView):
    def get(self, request, username):
        """
        确认订单页视图逻辑
        购物车: http://127.0.0.1:8000/v1/orders/zhaoliying/advance?settlement_type=0
        立即购买:http://127.0.0.1:8000/v1/orders/zhaoliying/advance?sku_id=1&buy_num=3&settlement_type=1
        查询字符串说明:
          settlement_type: 0(购物车) 1(立即购买)
          sku_id: 商品id(立即购买)
          buy_num: 商品数量(立即购买)
        """
        # 1.获取地址数据
        myuser = request.myuser
        addresses = self.get_order_addresses(myuser)

        # 2.获取商品数据
        settlement_type = request.GET.get("settlement_type")
        if settlement_type == "0":
            # 购物车链条
            sku_list = self.get_cart_sku_list(myuser.id)
        else:
            # 立即购买链条
            sku_id = request.GET.get("sku_id")
            buy_num = request.GET.get("buy_num")

            # 复用购物车中的方法
            carts_dict = {sku_id: [int(buy_num), 1]}
            sku_list = CartsView().get_skus_list(carts_dict)

        result = {
            "code": 200,
            "data": {
                "addresses": addresses,
                "sku_list": sku_list
            },
            "base_url": settings.PIC_URL
        }

        return JsonResponse(result)

    def get_order_addresses(self, myuser):
        """
        功能函数:获取用户的所有收货地址
        :param myuser: 用户对象
        :return: [{默认地址的字典},{},{}]
        """
        user_address = Address.objects.filter(user_profile=myuser, is_active=True)
        addresses = []
        for user_addr in user_address:
            user_addr_dict = {
                "id": user_addr.id,
                "name": user_addr.receiver,
                "mobile": user_addr.receiver_mobile,
                "title": user_addr.tag,
                "address": user_addr.address
            }
            if user_addr.is_default:
                addresses.insert(0, user_addr_dict)
            else:
                addresses.append(user_addr_dict)

        print('---->', addresses)
        return addresses

    def get_cart_sku_list(self, user_id):
        """
        功能函数: 购物车链条获取商品相关数据
        :return: [{},{},....]
        """
        # {"1":[10,1], "2":[20,1], "3":[40,0]}
        carts_dict = CartsView().get_carts_dict(user_id)
        carts_dict = {k: v for k, v in carts_dict.items() if v[1] == 1}  # 只要选中状态的也就是为1的，因为确认订单是使用的购物车中选中状态的，可以看界面

        return CartsView().get_skus_list(carts_dict)


class OrderInfoView(BaseView):
    def post(self, request, username):
        """
        生成订单视图逻辑  注意并发问题
        1.获取请求体数据
        2.三个ORM操作
          2.1 订单表中插入数据(OrderInfo)
          2.2 更新库存和销量(SKU)
          2.3 订单商品表中插入数据(OrderGoods)
        3.组织数据返回
        """

        mydata = request.mydata
        address_id = mydata.get("address_id")
        myuser = request.myuser

        try:
            addr = Address.objects.get(id=address_id, is_active=True, user_profile=myuser)
        except Exception as e:
            return JsonResponse({"code": 10400, "error": "地址不存在!"})

        # order_id: 时间戳+用户id
        order_id = time.strftime("%Y%m%d%H%M%S") + str(myuser.id)
        total_amount = 0
        total_count = 0

        with transaction.atomic():  #Django 事务transaction.atomic(),遇到错误执行回滚操作，类似mysql回滚函数,防止下订单并发导致一直变动的问题
            sid = transaction.savepoint()
            # 操作1: 订单表中插入数据
            order = OrderInfo.objects.create(user_profile=myuser, order_id=order_id, total_amount=total_amount, total_count=total_count, pay_method=1, freight=0, status=1,receiver=addr.receiver, address=addr.address, receiver_mobile=addr.receiver_mobile, tag=addr.tag)

            # 操作2: 更新SKU库存和销量
            carts_dict = CartsView().get_carts_dict(myuser.id)
            # carts_dict: {"1":[8,1], "2":[6,1]}
            # carts_1 - {'sku_id':[count,select]}
            carts_dict = {k: v for k, v in carts_dict.items() if v[1] == 1}
            skus = SKU.objects.filter(id__in=carts_dict.keys())
            for sku in skus:
                # 1.校验上架状态
                if not sku.is_launched:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({"code": 10400, "error": f"{sku.name}已下架~~~"})

                # 2.校验库存
                # count = carts_dict[str(sku.id)][0] #key error
                count = carts_dict[int(sku.id)][0]
                if count > sku.stock:
                    #库存不足，回滚
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({"code": 10401, "error": f"{sku.name}库存量不足,仅剩{sku.stock}件"})

                # 更新库存和销量，通过对当前version进行控制，因为sku.stock一直在变，再次使用上次查询参数sku.version，version=old_version进行新的查询，失败则代表这段时间更改过库存，更新失败，回滚。这里类似乐观锁
                old_version = sku.version
                result = SKU.objects.filter(id=sku.id, version=old_version).update(
                    stock=sku.stock - count,
                    sales=sku.sales + count,
                    version=old_version + 1
                )
                if result == 0: #version=old_versionc查询失败，导致更新失败
                    # 库存发生变化,回滚
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({"code": 10104, "error": "并发异常~~"})

                # 操作3: 订单商品表中插入数据
                OrderGoods.objects.create(order_info_id=order_id, sku_id=sku.id, count=count, price=sku.price)

                total_amount += sku.price * count
                total_count += count

            order.total_amount = total_amount
            order.total_count = total_count
            order.save()

            # 提交事务
            transaction.savepoint_commit(sid)

        # 删除购物车中已经转化为订单的商品的数据(Redis)
        all_carts_dict = CartsView().get_carts_dict(myuser.id)
        new_carts_dict = {k: v for k, v in all_carts_dict.items() if v[1] == 0}
        key = f"carts_{myuser.id}"
        CARTS_CACHE.set(key, new_carts_dict)

        # 组织数据返回
        result = {
            "code": 200,
            "data": {
                'saller': '达达商城',
                'total_amount': total_amount,
                'order_id': order_id,
                'pay_url': self.get_pay_url(order_id, float(total_amount)),
                'carts_count': len(new_carts_dict),
            }
        }

        return JsonResponse(result)

    def get(self, request, username):
        """
        查询订单视图逻辑
        1.获取查询字符串 type=?
        0 - 查看所有订单
        1 - 查看待付款订单
        2 - 查看待发货订单
        3 - 查看待收货订单
        4 - 查看已完成订单
        5 - 去付款
        """
        status = request.GET.get("type")
        myuser = request.myuser

        if status == "0":
            # 全部订单
            orders_query = OrderInfo.objects.filter(user_profile=myuser)
        elif status == "5":
            # 	http://127.0.0.1:8000/v1/orders/zhaoliying?type=5&order_id=202205241718508
            # 去付款逻辑
            order_id = request.GET.get("order_id")
            try:
                order = OrderInfo.objects.get(order_id=order_id)
            except Exception as e:
                return JsonResponse({"code": 10402, "error": "该订单不存在~~"})

            new_carts_dict = CartsView().get_carts_dict(myuser.id)
            result = {
                "code": 200,
                "data": {
                    'saller': '达达商城',
                    'total_amount': order.total_amount,
                    'order_id': order_id,
                    'pay_url': self.get_pay_url(order_id, float(order.total_amount)),
                    'carts_count': len(new_carts_dict),
                }
            }

            return JsonResponse(result)
        else:
            # 对应状态的订单(待付款、待发货、待收货、已完成)
            orders_query = OrderInfo.objects.filter(user_profile=myuser, status=int(status))

        # 组织数据返回
        order_list = []
        for order in orders_query:
            # 获取该订单中所有的商品
            order_goods = OrderGoods.objects.filter(order_info=order)
            order_sku = []
            for goods_sku in order_goods:
                sku = goods_sku.sku
                value_query = sku.sale_attr_value.all()
                sku_dict = {
                    "id": sku.id,
                    "default_image_url": str(sku.default_image_url),
                    "name": sku.name,
                    "price": sku.price,
                    "count": goods_sku.count,
                    "total_amount": sku.price * goods_sku.count,
                    "sku_sale_attr_names": [i.spu_sale_attr.name for i in value_query],
                    "sku_sale_attr_vals": [i.name for i in value_query]
                }
                order_sku.append(sku_dict)

            order_dict = {
                "order_id": order.order_id,
                "order_total_count": order.total_count,
                "order_total_amount": order.total_amount,
                "order_freight": order.freight,
                "address": {
                    "title": order.tag,
                    "address": order.address,
                    "mobile": order.receiver_mobile,
                    "receiver": order.receiver
                },
                "status": order.status,
                "order_sku": order_sku,
                "order_time": str(order.created_time)[:19]
            }
            order_list.append(order_dict)

        result = {
            "code": 200,
            "data": {"orders_list": order_list},
            "base_url": settings.PIC_URL
        }

        return JsonResponse(result)

    def put(self, request, username):
        """
        确认收货视图逻辑
        将订单的状态 由 3 改为 4 即可(一查二改三保存)
        """
        order_id = request.mydata.get("order_id")
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return JsonResponse({"code": 10403, "error": "该订单不存在~~"})

        order.status = 4
        order.save()

        return JsonResponse({"code": 200})

    def get_pay_url(self, order_id, total_amount):
        """
        功能函数:生成第三方支付的地址
        """
        # 1.初始化alipay对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_string=open(settings.ALIPAY_KEYS_DIR + "app_private_key.pem").read(),
            alipay_public_key_string=open(settings.ALIPAY_KEYS_DIR + "alipay_public_key.pem").read(),
            sign_type="RSA2",
            debug=True
        )
        # 2.调用方法
        params = alipay.api_alipay_trade_page_pay(
            subject=order_id,
            out_trade_no=order_id,
            total_amount=total_amount,
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=settings.ALIPAY_NOTIFY_URL
        )

        # 支付宝网关 + 查询字符串
        return "https://openapi.alipaydev.com/gateway.do?" + params

