# dashopt

参考bilibili视频，与视频略有不同复现电商后端，

前端是拿的不完全匹配的视频源码，我自己根据报错改了一些内容...其实后端也和视频不完全一致,

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





### 一些部署后发现的记录错误与解决：

使用natapp内网穿透（一天）:

出现Access to XMLHttpRequest at 'http://127.0.0.1:8009/v1/goods/index' from origin 'http://aqcfxd.natappfree.cc' has been blocked by CORS policy: The request client is not a secure context and the resource is in more-private address space `local`.

解决:思路 jsonp,或者 做代理或改dns,两种资源都改成内网或者外网ip ,比如nginx代理apache(我原先的博客这么做的没报错)  或者跨域响应头加Access-Control-Allow-Private-Network 或者https 或者chrome://flags/#block-insecure-private-network-requests 设置disabled

最后:chrome://flags/#block-insecure-private-network-requests 或者设置disabled生效 ;修改baseUrl为8010,再nginx代理8010->8009
都可以访问，后续都引发了jwttoken失效问题（后面有解决），并且速度特别慢 -放弃本地部署的考虑。

git到服务器apache部署，配置同httpd.conf：

后续： 尝试虚拟主机部署（3天）--单个虚拟主机成功：配置参考我的博客项目里的httpd-blogxnzj.conf和httpd-vhosts-blogxnzj.conf

 1.无法同时loadfile两组modwsgi.pyd;如果modwsgi和python版本不一致则更麻烦；我这里都是不同环境的python3.6,所以给一组

 2.windows是mpm,无法使用守护进程，只能嵌入式

 3.使用嵌入式，httpd.conf里同时给出两个项目的虚拟环境，根据官网;/:分隔也不行，无法启动apache,会提示错误，并且使用wsgialias必须有pythonhome,还不能不带一个，不能纯python脚本指定；根据官网尝试在脚本里添加虚拟环境和项目路径，成功可以启动，但第二个虚拟环境无法生效，只能访问一开始带的pythonhome对应项目，所以一个httpd.conf，启动多个环境不同的虚拟主机：第二个失败，第二个虚拟环境不生效。

最后使用指定不同名字的httpd.conf来启动http.exe，分别启动两个不同环境的服务--成功在同一个ip的apache服务器上，部署两个项目。

建议同环境的项目同一个http.conf,并且可以多开虚拟主机来提高并发；不同环境的还是每个服务各自一个http.conf启动，并且不会互相影响。



debug:外网访问，使用浏览器开发者工具，发现一些固定写死的ip导致的资源访问错误，查看引用和来源，修正为服务器ip(init.js和settings_apache.py的)

debug:服务器部署后，使用手访问发现token还是失效，原因Apache 抛弃了 Authorization 的 HTTP Header 头导致的，需要对其配置WSGIPassAuthorization On。





### 使用：

[本项目地址](http://101.34.15.153:8008)

地址：登录用户：用户名 dadashop  密码 123456   （未开放注册,荣联云只自己的手机作为短信验证注册测试，所以别注册了）

商品：只有一个spu的三个sku数据：名字是手提包，详情页分别是skuid=1 2 3,详情页只有加购物车或者购买两个路由

购物车：一个在本地浏览器，一个在redis,登录后会合并

前端页面部分路由不生效请忽略

不会放很久









可选开发工具：postman，apifox(中文的)，比自己写的python的requests模块脚本好用



[树莓博客网](http://101.34.15.153)
berryha.comberryha.com

爬虫的兄弟们千万不要爬我的，练手也不要，小服务器。。。

当下进行中的：正在尝试drf进行一个图像识别处理ocr+facerecognition 及Workflow工作流，BPM与RPA 结合

csdn   fireworkseasycold

欢迎来信留言qq.com 1476094297@qq.com

另外：找工作中，欢迎小伙伴提供苏州python的后端工作机会
