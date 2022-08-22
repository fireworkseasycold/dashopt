import redis
from django.http import HttpResponse, JsonResponse
from goods.models import SKU


r = redis.Redis(host="localhost", port=6379, db=0)


def cors_view(request):
    """测试cors跨域"""
    return HttpResponse("九霄龙吟惊天变,cors is ok")


def stock_view(request):
    """测试Redis分布式锁"""
    # 加锁
    # with r.lock("dashopt:stock", blocking_timeout=5) as lock:
    sku = SKU.objects.get(id=1)
    sku.stock -= 1
    sku.save()

    return JsonResponse({"code": 200})









