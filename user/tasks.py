from django.conf import settings
from django.core.mail import send_mail
from dashopt.celery import app
from utils.smsapi import ShortMessageAPI


@app.task
def async_send_active_email(email, verify_url):
    """
    功能函数：发送激活邮件
    """
    subject = "达达商城激活邮件"
    html_message = """
    尊敬的用户您好,请点击链接进行激活~~~
    <a href="%s" target="_blank">点击此处</a>
    """ % verify_url

    send_mail(subject=subject,
              message="",
              from_email=settings.EMAIL_HOST_USER,
              recipient_list=[email],
              html_message=html_message
              )


@app.task
def async_send_message(phone_number, sms_code, expire_time):
    smapi = ShortMessageAPI(**settings.SMS_CONFIG)
    smapi.send_message(phone_number, sms_code, expire_time)













