from django.db import models

# Create your models here.


#购物车请求量大数据量大，价值低，所以不放mysql直接放redis
"""
购物车数据
cart_id:
{
    sku_id:{
        'count':'xxxx',  #一个sku的数目
        'selected':0或者1,  #是否勾选的状态
        ...
        },
    sku_id:{
    'count':'xxxx',  #一个sku的数目
    'selected':0或者1,  #是否勾选的状态
    ...
    },
    ...

    #如果dict太占地，也可以将字典换用列表
    sku_id:['countvalue','selectedvalue',...]
}

满足需求的redis数据结构有string&hash这两个结构
使用string:  r.set(json.dumps({ sku_id:['countvalue','selectedvalue',...]}) #整体序列化一下放进去，对象转str,必须保证存进去的是str
            r.get(json.loads())  整体存整体取
             string也可以用django的cache.set和get方法，这里不用再写序列化了，因为cache源码写了


使用hash r.hset(cart_id,sku_id,json.dumps(['countvalue','selectedvalue',...])
        哈希可以按需获取，但是这里基本上都是获取所有

所以最后用string


登录&非登录
1.登录-》存redis
2.非登录-》存浏览器-》cookie或者本地存储，这里弃用cookie选本地存储
难点：登陆时把浏览器购物车合并到redis
    登录/注册操作时，前端上传的数据中，包含了一个carts key,该key对应的值即为浏览器本地存储中的购物车数据
"""
