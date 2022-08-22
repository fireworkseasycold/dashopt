"""
    进阶版的装饰器：构建可传参的装饰器
"""
from django.core.cache import caches

#怎么存，仿照官方cache_page
def cache_check(**cache_kwargs):
    def _cache_check(func):
        def wrapper(self, request, *args, **kwargs):
            """
            :params cache_kwargs: 装饰器参数
            :params func: 被装饰的方法
            :params self,request,*args,**kwargs: 方法参数
            """
            # cache_kwargs:{'key_prefix': 'gd', 'key_param': 'sku_id', 'cache': 'goods_detail', 'expire': 60}
            # kwargs:{'sku_id': 1}
            # 1.先确认缓存中是否存在数据
            # 2.缓存中存在,则直接返回
            # 3.缓存中不存在,走视图并将数据缓存到Redis中

            #获取缓存区（caches[缓存空间名]等同于CACHE）
            if "cache" in cache_kwargs:
                redis_cache = caches[cache_kwargs.get("cache")]  #这里获取settinsg里对应的goods_detail缓存空间
            else:
                redis_cache = caches["default"]
            #检查缓存
            key = cache_kwargs.get("key_prefix") + str(kwargs.get("sku_id"))
            response = redis_cache.get(key)
            if response:
                # 缓存中存在数据
                print('~~~data from redis,Oh Yeah~~~')
                return response

            # 缓存中没有数据,则到MySQL中查询数据
            mysql_response = func(self, request, *args, **kwargs)

            # 缓存到redis中一份,默认60s
            expire = cache_kwargs.get("expire", 60)
            redis_cache.set(key, mysql_response, expire)

            return mysql_response
        return wrapper
    return _cache_check

























