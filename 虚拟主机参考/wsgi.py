"""
WSGI config for berryhablog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import site
import sys

from django.core.wsgi import get_wsgi_application

#apache+modwsgi,虚拟主机部署添加代码
# 这是官方mod——wsgi venv的写法
# activate_this = python_home + '/bin/activate_this.py'
# execfile(activate_this, dict(__file__=activate_this))
#但是我这里是conda,无activate_this.py
python_home = 'C:/ProgramData/Anaconda3/envs/berryhablog'
site.addsitedir(python_home)  #虚拟环境路径
# os.system('conda activate berryhablog')  #本来想使用命令实现上面的功能的，不行


# sys.path.append('xxxxxxx')  #如提示无法导入ModuleNotFoundError: No module named 'mysite'\r, referer: http://localhost:8002/，可按照示例增加此路径
sys.path.append('C:/myproject/berryhablog')
sys.path.append('C:/myproject/berryhablog/mysite')





os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

application = get_wsgi_application()
