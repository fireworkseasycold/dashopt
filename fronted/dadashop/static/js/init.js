// 线上的URL
//baseUrl="http://114.116.244.115:7000"
// 本地测试django_URL
//baseUrl="http://127.0.0.1:8000"

// 本地测试nginx_URL
NbaseUrl="http://127.0.0.1"

// 本地图片BASEURL
//imgUrl= "http://127.0.0.1:8000/media/"

//我后来本地部署添加的，注释掉上面俩
// 部署django_URL
baseUrl="http://127.0.0.1:8009"
// 部署的服务图片BASEURL
//imgUrl= "http://127.0.0.1:8009/media/"  //这样使用apache端口使用apache端作为图片服务器（需要apache的media配置）
imgUrl= "http://127.0.0.1:8008/media/"  //这里使用nginx端口nginx来为media服务器(需要nginx配置medai),性能更好.
//imgUrl经过查看调用,并执行调用看日志,以及各种端口组合,发现个imgUrl其实只有在用于不登录的时候添加购物车才使用,属于来自静态文件服务器图片路径,
//所以imgUrl必须和部署时候settings_apache.py里的PIC_URL一致（pycharm查看PIC_URL被引用发现PIC_URL会返回给前端,也是属于来自静态文件服务器图片路径）