# 使用celery
from django.core.mail import send_mail
from django.conf import settings
from celery import Celery
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()
# 创建一个Celery类的实例对象

app = Celery('celery_tasks.tasks', broker='redis://192.168.199.250:6379/8')
@app.task
def send_register_active_email(to_email, username, token):
    # 发邮件
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    htmlmessage = '<h1>尊敬的%s，欢迎您成为天天生鲜会员</h1>请点击下面地址进行注册</br><a href="http://192.168.199.251:8000/user/active/%s">http://192.168.199.251:8000/active/%s</a>' % (
    username, token, token)
    send_mail(subject, message, sender, receiver, html_message=htmlmessage)
