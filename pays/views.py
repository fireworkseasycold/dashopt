from alipay import AliPay
from django.conf import settings
from django.views import View
from django.http import JsonResponse, HttpResponse

from orders.models import OrderInfo


class MyAlipay(View):
    """
    支付基类,用于初始化Alipay对象并提供常用方法
    其他视图类继承此基类后可以使用类内任何方法及属性
    """
    def __init__(self, **kwargs):
        # 1.不能影响父类(View)的初始化
        super().__init__(**kwargs)
        # 2.初始化Alipay对象
        self.alipay = AliPay(
            # 应用ID:控制台中获取
            appid=settings.ALIPAY_APPID,
            # 异步通知地址
            app_notify_url=None,
            # 应用私钥[用于签名]
            app_private_key_string=open(settings.ALIPAY_KEYS_DIR + "app_private_key.pem").read(),
            # alipay公钥[用于验签]
            alipay_public_key_string=open(settings.ALIPAY_KEYS_DIR + "alipay_public_key.pem").read(),
            # 签名使用算法
            sign_type="RSA2",
            # True请求转发至沙箱 False直接发至生产环境
            debug=True
        )


class ReturnUrlView(MyAlipay):
    def get(self, request):
        """
        同步通知视图逻辑return_url[没有支付结果,只有支付信息]
        1.获取支付信息(查询字符串)
        2.无需验签
        3.主动查询支付结果(接口文档)
        """
        request_data = request.GET
        # 订单号、支付宝交易号
        out_trade_no = request_data.get("out_trade_no")
        trade_no = request_data.get("trade_no")
        # response: 查看接口文档
        response = self.alipay.api_alipay_trade_query(out_trade_no, trade_no)
        status = response.get("trade_status")
        if status == "TRADE_SUCCESS":
            # 交易成功,处理订单
            order = OrderInfo.objects.get(order_id=out_trade_no)
            order.status = 2
            order.save()
            return HttpResponse("GET 主动查询,交易成功")
        else:
            return HttpResponse("GET 主动查询,交易失败")


class NotifyUrlView(MyAlipay):
    def post(self, request):
        """
        异步通知视图逻辑[存在支付结果]
        1.获取请求体数据
        2.验签
        3.获取支付结果
          根据支付结果的状态修改订单状态
        """
        request_data = request.POST
        sign = request_data.pop("sign")

        # verify():验签True|False
        result = self.alipay.verify(request_data, sign)
        if result:
            # 验签成功,获取支付结果,调整订单状态
            status = request_data.get("trade_status")
            if status == "TRADE_SUCCESS":
                # 修改订单状态
                order_id = request_data.get("out_trade_no")
                order = OrderInfo.objects.get(order_id=order_id)
                order.status = 2
                order.save()
                return HttpResponse("success")
        else:
            return HttpResponse("违法请求~~")




