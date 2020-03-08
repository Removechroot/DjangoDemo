from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from user.models import User, Address
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequiresMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
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
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接过期
            return HttpResponse('激活已过期')


# 用户登陆处理
class LoginView(View):
    def get(self, request):
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
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 业务处理
        user = authenticate(username=username, password=password)  # 如果里面数据正确返回
        if user is not None:
            if user.is_active:
                login(request, user)
                # 获取登陆后要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                res = redirect(next_url)
                # 判断是否记住用户名
                remeber = request.POST.get('remeber')
                if remeber == 'on':
                    res.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    res.delete_cookie('username')
                # 页面跳转
                return res
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})

        else:
            return render(request, 'login.html', {'errmsg': '账户或密码错误'})


# 用户登出处理
class LogoutView(View):
    def get(self, request):
        # 清除用户session
        logout(request)
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiresMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='192.168.199.250',db=5)
        con = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询用户浏览的商品具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiresMixin, View):
    def get(self, request):
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class AddressView(LoginRequiresMixin, View):
    def get(self, request):
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号码错误'})
        # 业务处理:地址添加
        # 001-地址查重
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone,
                               is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address'))
