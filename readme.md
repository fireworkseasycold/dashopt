# dashopt


参考bilibili视频，与视频略有不同复现电商后端，前端是拿的不完全匹配的视频源码

[视频地址](https://www.bilibili.com/video/BV1ee411p7LD?spm_id_from=333.999.0.0&vd_source=16c42409242358fc5a48ba5c09dc17a0)

### django原生前后端分离



环境管理：anaconda
conda create xxxx python=3.6/3.7  #建议3.7，因为3.6已经停止维护了，现在最新3.10

pip install django2.2-3.2.14 redis(我的博客下有windows安装包) django-cors-headers pymsql modwsgi celery等等

### app

user  jwttoken 注册登录

goods   变动即更新缓存

carts  使用redis而不是mysql存储，注意未登录时浏览器购物车与登陆后redis购物车合并

orders    使用事务管理，通过节点来防止并发时候的订单错误

与我的博客使用装饰器的缓存页面与查询集合以及单独装饰器判断登录相比，

优点：本项目新建的BaseView（View）里封装了redis缓存以及更新则清理goods库的功能，以及登录状态的判断然后给部分视图类继承；还有订单内使用了django的事务管理功能来解决并发下goods库存一直变动导致的问题。

同样使用celery执行异步任务

感觉本项目唯一的就是缓存这块，事务，以及购物车这块还行。

方法太原生了。。。还是drf代码简洁方便



### 数据

mysql+redis   

导入goods_data.json

可以优化：根据实际精简model字段长度



### 部署：

本地电脑+内网穿透工具（家里宽带不用内网穿透一般外网用不了，注意如果使用路由器也可能有影响

/(ㄒoㄒ)/~~，还是云服务器好用，服务器ip+端口或者dns解析了的域名）

1.前端  ->nginx（自行配置）

2.后端-> apache（自行配置）

3.nginx->apache

注意前端端口和后端端口

未采用虚拟主机，实际有需要自己配置并使用轮询来提高并发功能

配置可以具体参考我的博客的配置文件

如果需要linux部署的，安装uwsgi,替换modwsgi与apache即可

后面看看腾讯的宝塔面板，好像更方便，写个shell脚本监控程序状态，比如





地址挂了说明我关了内网穿透，

用户：（未开放注册）使用dadashop  密码123456

商品：只有一个spu的三个sku数据：手提包，详情页分别是skuid=1 2 3



前端页面部分路由不生效请忽略







可选开发工具：postman，apifox(中文的)，比自己写的python的requests模块脚本好用



[树莓博客网](thhp://101.34.15.153)

csdn   fireworkseasycold

欢迎来信留言qq.com 1476094297@qq.com

另外：找工作中，欢迎小伙伴提供苏州python的后端工作机会


