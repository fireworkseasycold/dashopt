import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashopt.settings")
app = Celery("dashop_group", broker="redis://:@127.0.0.1:6379/15")
app.autodiscover_tasks(settings.INSTALLED_APPS)



















