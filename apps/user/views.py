from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from user.models import User
from django.core.mail import send_mail
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login
import re

# Create your views here.
'''def register(request):
    if request.method == 'GET':

        # 显示登陆页面
        return render(request, 'register.html')
    else:
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        allow = request.POST.get('allow')
        email = request.POST.get('email')
        # 1.进行数据校验
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':

            render(request, 'register.html', {'errmsg': '请同意用户协议'})
        # 2.进行业务处理，进行用户注册
        # 校验用户名是否重复
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
            # 用户已存在
            if user:
                return render(request, 'register.html', {'errmsg:用户已存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 3.返回应答
        return redirect(reverse('goods:index'))
def register_handle(request):
    # 登陆处理&&接受数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    allow = request.POST.get('allow')
    email = request.POST.get('email')
    # 1.进行数据校验
    if all([username, password, email]):
        return render(request, 'register.html', {'errmsg': '数据不完整'})
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
    if allow != 'on':
        
        render(request, 'register.html', {'errmsg': '请同意用户协议'})
    # 2.进行业务处理，进行用户注册
    # 校验用户名是否重复
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
        # 用户已存在
        if user:
            return render(request, 'register.html', {'errmsg:用户已存在'})

    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()
    # 3.返回应答
    return redirect(reverse('goods:index'))'''

class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')
    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        allow = request.POST.get('allow')
        email = request.POST.get('email')
        # 1.进行数据校验
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':

            render(request, 'register.html', {'errmsg': '请同意用户协议'})
        # 2.进行业务处理，进行用户注册
        # 校验用户名是否重复
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
            # 用户已存在
            if user:
                return render(request, 'register.html', {'errmsg:用户已存在'})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 生成用户加密信息，加密token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        # 发邮件
        send_register_active_email.delay(email, username, token)
        # 3.返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        '''进行用户激活'''
        # 解密，获取激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        print(token)
        try:
            info = serializer.loads(token)
            # 获取激活用户ID
            user_id = info['confirm']
            user = User.objects.get(id = user_id)
            user.is_active = 1
            user.save()
            # 跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接过期
            return HttpResponse('激活已过期')
class LoginView(View):
    def get(self,request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})
    def post(self, request):
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整'})
        # 业务处理
        user = authenticate(username=username, password=password) # 如果里面数据正确返回
        if user is not None:
            if user.is_active:
                login(request, user)
                res =  redirect(reverse('goods:index'))
                # 判断是否记住用户名
                remeber = request.POST.get('remeber')
                if remeber == 'on':
                    res.set_cookie('username', username, max_age=7*24*3600)
                else:
                    res.delete_cookie('username')
                # 页面跳转
                return res
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})

        else:
            return render(request, 'login.html', {'errmsg':'账户或密码错误'})
