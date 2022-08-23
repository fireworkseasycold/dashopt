# dashopt


参考bilibili视频，与视频略有不同复现电商后端，前端是拿的不完全匹配的视频源码...其实后端也和视频不完全一致,我当初参考做的是另一个视频不过挂了

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

1.前端  ->nginx（自行配置）8008
    添加nginx配置
    发现前端访问baseUrl都不是后端接口:
    解决:全局查询调用,修改init.js baseUrl 为后端部署接口
    
    

2.后端-> apache（自行配置）8009，当然你也可以不改就用8000
    添加apache配置
    修改settings.py里DEBUG=False来加载部署用的settings_apache.py
    修改settings_apache.py里所有不对的url路径
    后面出现后端8009/media/sku图片404解决： 此时settings_apache.py PIC_URL = 'http://127.0.0.1:8009' + MEDIA_URL
    settings_apache.py里的 PIC_URL #查看PIC_URL被引用对象(Alt+F7),发现会改对象会放到json里返回给前端,是图片服务器返回的图片路径
    所以需要配置图片服务器,
    在apache配置项里添加media：
    Alias /media/ D:/2202/day12_all/dashopt/media/
    <Directory D:/2202/day12_all/dashopt/media>
    AllowOverride None
    Options None
    Require all granted
    </Directory>
    个人感觉如果这样做用apache作为图片服务器太拉了,因为nginx性能更好
    所以改settings_apache.py PIC_URL = 'http://127.0.0.1:8008' + MEDIA_URL来nginx作为静态服务器
    另外-发现init.js的imgUrl经过全项目查找查看调用,并执行调用看日志,以及各种端口组合,发现imgUrl其实只有在用于不登录的时候添加购物车才使用,它也是属于来自静态文件服务器图片路径,
    所以必须要修改init.js 的 baseUrl 与 settings_apache.py PIC_URL 的 PIC_URL一致,都是图片服务器路径
    配置nginx media
    location /media/ {
            root D:/2202/day12_all/dashopt; #此处为Django中设置的mediaroot文件夹位置
        }
    
   
3.nginx<->apache

注意前端端口和后端端口

未采用虚拟主机，实际有需要自己配置并使用轮询来提高并发功能

配置可以具体参考我的博客的配置文件

如果需要linux部署的，安装uwsgi,替换modwsgi与apache即可

后面看看腾讯的宝塔面板，好像更方便，写个shell脚本监控程序状态


本地使用natapp内网穿透:
出现Access to XMLHttpRequest at 'http://127.0.0.1:8009/v1/goods/index' from origin 'http://aqcfxd.natappfree.cc' has been blocked by CORS policy: The request client is not a secure context and the resource is in more-private address space `local`.
解决:思路 jsonp,或者 做代理或改dns,两种资源都改成内网或者外网ip ,比如nginx代理apache(我原先的博客这么做的没报错)  或者跨域响应头加Access-Control-Allow-Private-Network 或者https 或者chrome://flags/#block-insecure-private-network-requests 设置disabled
最后:chrome://flags/#block-insecure-private-network-requests 或者设置disabled生效 ;修改baseUrl为8010,再nginx代理8010->8009
但是都引发了jwttoken失效问题
放弃,前端提示网页被修改，貌似是类似local class serialVersionUID本地和远程不一致导致的错误
最后尝试apache部署虚拟主机部署来多个django项目（因为已经有了博客）
看了官网modwsgi的，首先只支持一个modwsgi...
后续实在太繁琐了，尤其我是不同的mod_wsgi还有不同的python版本虚拟环境，不停修改根据报错测试两天。。。卒
还是用iis



登录用户：（未开放注册,荣联云我只添加弄了自己的手机作为短信验证注册测试）用户名 dadashop  密码 123456 

商品：只有一个spu的三个sku数据：手提包，详情页分别是skuid=1 2 3,别管界面上的可选,直接在详情页加购物车或者购买
前端页面部分路由不生效请忽略

右上角的几个图标都是可以点击的,分别是地址,订单,购物车,用户







可选开发工具：postman，apifox(中文的)，比自己写的python的requests模块脚本好用



[树莓博客网](thhp://101.34.15.153)

csdn   fireworkseasycold

欢迎来信留言qq.com 1476094297@qq.com

另外：找工作中，欢迎小伙伴提供苏州python的后端工作机会


