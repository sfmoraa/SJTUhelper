import time

import requests
from django.shortcuts import render, HttpResponse, redirect
from app01.models import *
from django.contrib.auth.models import User
from django.contrib import auth
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.http import JsonResponse

print("views running")
from combined import *
import threading

lock_cookies = threading.Lock()
lock_canvas = threading.Lock()
lock_dekt = threading.Lock()
lock_calendar = threading.Lock()
lock_shuiyuan = threading.Lock()
lock_weibo = threading.Lock()
lock_github = threading.Lock()
lock_bilibili = threading.Lock()
lock_zhihu = threading.Lock()
lock_weather = threading.Lock()
lock_seiee = threading.Lock()


# Create your views here.
def index(request):
    return HttpResponse("欢迎使用")


''' *********************** 定时任务 *********************** '''


def test_job():
    print("running!", strftime("%Y-%m-%d %H:%M:%S", localtime()))
    try:
        get_zhihu_hot_topic(lock=lock_zhihu,
                            cookie='_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410')
    except:
        print("get_zhihu_hot_topic FAILED")
    try:
        get_github_trending(lock=lock_github)
    except:
        print("gget_github_trending FAILED")
    try:
        get_weibo_hot_topic(lock=lock_weibo)
    except:
        print("get_weibo_hot_topic FAILED")
    try:
        get_minhang_24h_weather(lock=lock_weather)
    except:
        print("get_minhang_24h_weather FAILED")
    try:
        get_bilibili_ranking(lock=lock_bilibili)
    except:
        print("get_bilibili_ranking FAILED")
    print("updated!", strftime("%Y-%m-%d %H:%M:%S", localtime()))


scheduler = BackgroundScheduler()
trigger = IntervalTrigger(seconds=60)
scheduler.add_job(test_job, trigger=trigger, id="update_data")
scheduler.start()


def sjtu_login(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    if request.method == "GET":
        return render(request, "jaccount.html")
    jaccount_user = request.POST.get("signin_usr")
    jaccount_pwd = request.POST.get("signin_pwd")
    status, msg = validate_account(jaccount_user, jaccount_pwd)
    if not status:
        print("FAILED due to", msg)
        return render(request,"jaccount.html",{"errormsg":"用户名或者密码不正确"})  # 重定向到主页，后续添加错误信息
    request.user.first_name = jaccount_user
    request.user.save()
    check_box = request.POST.get('check_box')
    '''*******************数据库添加表单：request.user（当前使用SJTUhelper的用户）；jaccount_user（jaccount用户名）；cookies（暂空）*******************'''
    thread1 = threading.Thread(target=process_canvas, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_canvas})
    thread1.start()
    thread2 = threading.Thread(target=process_dekt, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_dekt})
    thread2.start()
    thread3 = threading.Thread(target=process_shuiyuan, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_shuiyuan})
    thread3.start()
    thread4 = threading.Thread(target=mysjtu_calendar, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_calendar})
    thread4.start()
    return redirect("http://127.0.0.1:8000/sjtu_login/")  # 重定向到主页




def show_calendar(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "calendar")
    thread = threading.Thread(target=mysjtu_calendar, kwargs={"username": jaccountname, 'lock': lock_cookies, 'lock1': lock_calendar})
    thread.start()
    data_list = gpt_filter(site="calendar_" + jaccountname, lock=lock_calendar, mode=1)
    schedule_data_json = []
    for schedule in data_list:
        schedule_data_json.append([schedule[1] + "[" + schedule[4] + "]", schedule[2], schedule[3], schedule[5], schedule[6]])
    print("json data to be used:", json.dumps(schedule_data_json))
    return render(request, "show_calendar.html", {"calendar_data_list": data_list})


def mytest(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    # reducedHotTopics1 = gpt_filter('zhihu', cue="我对军事政治不感兴趣", lock=lock_zhihu)
    # reducedHotTopics2 = gpt_filter('github', cue=None, lock=lock_github)
    # reducedHotTopics3 = gpt_filter('bilibili', cue="我想获得小于10条内容", lock=lock_bilibili)
    reducedHotTopics4 = gpt_filter('weibo', lock=lock_weibo, mode=1)
    # reducedHotTopics8 = gpt_filter("seiee_notion", lock=lock_seiee)
    # reducedHotTopics9 = gpt_filter("minhang_weather", lock=lock_weather)
    reducedHotTopics1 = []
    reducedHotTopics2 = []
    reducedHotTopics3 = []
    # reducedHotTopics4 = []
    reducedHotTopics8 = []
    reducedHotTopics9 = []
    return render(request, "mytest.html", {"zhihuHotTopic": reducedHotTopics1, "github": reducedHotTopics2, "bilibili": reducedHotTopics3, "weibo": reducedHotTopics4, "seiee_notion": reducedHotTopics8, "minhang_weather": reducedHotTopics9})


def tpl(request):
    name = "韩超"
    roles = ["管理员", "CEO", "保安"]
    user_info = {"name": "郭智", "salary": 100000, 'role': "CTO"}

    data_list = [
        {"name": "郭智", "salary": 100000, 'role': "CTO"},
        {"name": "卢慧", "salary": 100000, 'role': "CTO"},
        {"name": "赵建先", "salary": 100000, 'role': "CTO"},
    ]
    return render(request, 'tpl.html', {"n1": name, "n2": roles, 'n3': user_info, "n4": data_list})


def something(request):
    # request是一个对象，封装了用户发送过来的所有请求相关数据

    # 1.获取请求方式 GET/POST
    print(request.method)

    # 2.在URL上传递值 /something/?n1=123&n2=999
    print(request.GET)

    # 3.在请求体中提交数据
    print(request.POST)

    # 4.【响应】HttpResponse("返回内容")，内容字符串内容返回给请求者。
    # return HttpResponse("返回内容")

    # 5.【响应】读取HTML的内容 + 渲染（替换） -> 字符串，返回给用户浏览器。
    return render(request, 'something.html', {"title": "来了"})

    # 6.【响应】让浏览器重定向到其他的页面
    # return redirect("https://www.sjtu.edu.cn")


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # 在这里可以执行其他激活成功后的操作，例如重定向到登录页面
        return redirect("http://127.0.0.1:8000/loginpage/")
    else:
        # 处理激活失败的情况，例如显示一个错误页面
        return render(request, 'info_add.html')


def log_out(request):
    uername = request.user.username
    auth.logout(request)
    return HttpResponse("用户{}已经成功退出".format(uername))


def send(request):
    if request.method=='POST':

        # current_site = get_current_site(request)
        # 发送激活邮件
        username=request.POST.get('username')
        email=request.POST.get('email')
        user=User.objects.filter(username=username,email=email)
        if not user:
            return JsonResponse({'message':'不存在此用户，请检查用户名或者邮箱'},status=400)
        token = get_random_string(length=6)
        request.session['verification_token'] = token
        import datetime
        request.session['verification_expiry'] = (timezone.now() + timezone.timedelta(minutes=5)).isoformat()
        mail_subject = '激活您的账号'
        # activation_link = f"http://{current_site.domain}/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/"
        # message = render_to_string('activation_email.html', {
        #     'user': user,
        #     'activation_link': activation_link,
        # })
        try:
            send_mail(mail_subject, f'这是你的邮箱验证码:'+token+'\n有效时间为5分钟', 'sjtuhelper@163.com', [email])

            return JsonResponse({'message': '邮箱验证码已发送,有限时间5分钟'})
        except:
            return JsonResponse({'message': '无效的请求方法,请检查邮箱是否格式正确'})
    else:
        return JsonResponse({'message': '无效的请求方法'}, status=400)


def loginpage(request):
    if request.method == "GET":
        return render(request, "sign.html")
    else:
        # print(request.POST)
        if 'signin' in request.POST:
            username = request.POST.get("signin_usr")
            password = request.POST.get("signin_pwd")
            user_obj = auth.authenticate(username=username, password=password)

            if not user_obj:
                return render(request, 'sign.html', {'error_message': '用户名或密码不正确'})
            else:
                auth.login(request, user_obj)
                thread1 = threading.Thread(target=get_zhihu_hot_topic, kwargs={'lock': lock_zhihu,
                                                                               'cookie': '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'
                                                                               })
                thread1.start()
                thread2 = threading.Thread(target=get_github_trending, kwargs={'lock': lock_github})
                thread2.start()
                thread3 = threading.Thread(target=get_weibo_hot_topic, kwargs={'lock': lock_weibo})
                thread3.start()
                thread4 = threading.Thread(target=get_bilibili_ranking, kwargs={'lock': lock_bilibili})
                thread4.start()
                thread5 = threading.Thread(target=seiee_notification, kwargs={'lock': lock_seiee})
                thread5.start()
                thread6 = threading.Thread(target=get_minhang_24h_weather, kwargs={'lock': lock_weather})
                thread6.start()
                return redirect("https://www.sjtu.edu.cn")

            # 用户名或密码不正确，返回登录页面并显示错误信息

        else:
            username = request.POST.get("signup_usr")
            pwd = request.POST.get("signup_pwd")
            repwd = request.POST.get("signup_repwd")
            email = request.POST.get("email")
            token = request.POST.get("token")
            if not (username and pwd and repwd and email and token):
                return JsonResponse({'message': '输入不允许有空值'}, status=400)
            if User.objects.filter(username=username):
                return JsonResponse({'message': '用户已经存在，尝试别的用户名'}, status=400)
            if pwd != repwd:
                return JsonResponse({'message': '两次密码不一致'}, status=400)

            if request.session.get('verification_token') != token:
                print(request.session.get('verification_token'),token)
                return JsonResponse({'message': '验证码错误'}, status=400)
            if request.session.get('verification_expiry') < timezone.now().isoformat():
                return JsonResponse({'message': '验证码过期'}, status=400)

            user = User(username=username, email=email)
            user.set_password(pwd)
            user.is_active = True
            user.save()
            return JsonResponse({'message': '注册成功'})



def changepassword(request):
    if request.method == "GET":
        return render(request, "changepassword.html")
    username=request.POST.get("username")
    email=request.POST.get('email')
    token=request.POST.get('token')
    password =request.POST.get('password')
    user = User.objects.filter(username=username, email=email)
    if not user:
        return JsonResponse({'message': '不存在此用户，请检查用户名或者邮箱'}, status=400)
    user=user.first()
    user.set_password(password)
    user.is_active=True
    print(request.session.get('verification_token'))
    if token!=request.session.get('verification_token'):
        return JsonResponse({'message':'验证码错误'}, status=400)
    if request.session.get('verification_expiry') < timezone.now().isoformat():
        return JsonResponse({'message':'验证码超时'}, status=400)
    user.save()
    return JsonResponse({'message':'修改成功'})


# views.py

from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.utils import timezone



def send_signup(request):
    if request.method=='POST':

        # current_site = get_current_site(request)
        # 发送激活邮件
        username=request.POST.get('username')
        pwd = request.POST.get("signup_pwd")
        repwd = request.POST.get("signup_repwd")
        email=request.POST.get('email')
        if not (username and pwd and repwd and email):
            return JsonResponse({'message': '输入不允许有空值'}, status=400)
        user=User.objects.filter(username=username)
        if user:
            return JsonResponse({'message':'用户已经存在，尝试别的用户名'},status=400)
        if pwd!=repwd:
            return JsonResponse({'message': '两次密码不一致'}, status=400)
        token = get_random_string(length=6)
        request.session['verification_token'] = token
        import datetime
        request.session['verification_expiry'] = (timezone.now() + timezone.timedelta(minutes=5)).isoformat()
        mail_subject = '激活您的账号'
        # activation_link = f"http://{current_site.domain}/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/"
        # message = render_to_string('activation_email.html', {
        #     'user': user,
        #     'activation_link': activation_link,
        # })
        try:
            send_mail(mail_subject, '这是你的邮箱验证码:'+token+'\n有效时间为5分钟', 'sjtuhelper@163.com', [email])
            return JsonResponse({'message': '邮箱验证码已发送,有效时间5分钟'})
        except:
            return JsonResponse({'message': '无效的请求方法,请检查邮箱是否格式正确'}, status=400)


    else:
        return JsonResponse({'message': '无效的请求方法'}, status=400)

def zhihu(request):
    if (request.method == "GET"):
        thread = threading.Thread(target=get_zhihu_hot_topic, kwargs={'lock': lock_zhihu,
                                                                      'cookie': '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'})
        thread.start()

        key = "我对军事政治不感兴趣"
        reducedHotTopics1 = gpt_filter('zhihu', cue=key, lock=lock_zhihu, mode=1)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"key": key,
                                                  "zhihuHotTopic": reducedHotTopics1,
                                                  "minhang_weather": weather[1:5]})
    else:
        key = request.POST.get("key")
        print(key)

        reducedHotTopics = gpt_filter('zhihu', cue=key, lock=lock_zhihu)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"zhihuHotTopic": reducedHotTopics, "key": key, "minhang_weather": weather[1:5]})


def github(request):
    if (request.method == "GET"):
        get_github_trending(lock=lock_github)
        key = "python"

        reducedHotTopics = gpt_filter('github', cue=key, lock=lock_github, mode=1)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"key": key,
                                                  "github": reducedHotTopics,
                                                  "minhang_weather": weather[1:5]})
    else:
        key = request.POST.get("key")
        print(key)

        reducedHotTopics = gpt_filter('github', cue=key, lock=lock_github)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"github": reducedHotTopics, "key": key, "minhang_weather": weather[1:5]})


def bilibili(request):
    if (request.method == "GET"):
        thread = threading.Thread(target=get_bilibili_ranking, kwargs={'lock': lock_bilibili})
        key = "我想获得小于10条内容"

        reducedHotTopics3 = gpt_filter('bilibili', cue=key, lock=lock_bilibili, mode=1)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"key": key,
                                                  "bilibili": reducedHotTopics3,
                                                  "minhang_weather": weather[1:5]
                                                  })


    else:
        key = request.POST.get("key")
        print(key)

        reducedHotTopics = gpt_filter('bilibili', cue=key, lock=lock_bilibili)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"bilibili": reducedHotTopics, "key": key, "minhang_weather": weather[1:5]})


def weibo(request):
    if request.method == "GET":
        thread = threading.Thread(target=get_weibo_hot_topic, kwargs={'lock': lock_weibo})
        thread.start()
        reducedHotTopics4 = gpt_filter('weibo', lock=lock_weibo, mode=1)
        key = ""

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"weibo": reducedHotTopics4, "key": key, "minhang_weather": weather[1:5]})
    else:
        key = request.POST.get("key")
        print(key)

        reducedHotTopics = gpt_filter('weibo', cue="", lock=lock_weibo)

        get_minhang_24h_weather(lock=lock_weather)
        weather = gpt_filter("minhang_weather", lock=lock_weather)

        return render(request, "main_menu.html", {"github": reducedHotTopics, "key": key, "minhang_weather": weather[1:5]})


def canvas(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "canvas")
    thread = threading.Thread(target=process_canvas, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_canvas})
    thread.start()
    data_list = gpt_filter("canvas_{}".format(jaccountname), lock=lock_canvas)
    for item in data_list:
        item[5] = mark_safe(item[5])
    get_minhang_24h_weather(lock=lock_weather)
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    return render(request, "main_menu.html", {"canvas_data_list": data_list, "minhang_weather": weather[1:5]})


def dekt(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "dekt")
    thread = threading.Thread(target=process_dekt, kwargs={"username": jaccountname, 'lock': lock_cookies, 'lock1': lock_dekt})
    thread.start()
    data_list = gpt_filter("dekt", cue=None, mode=1, lock=lock_dekt)
    for item in data_list:
        item[5] = str(item[5])
    get_minhang_24h_weather(lock=lock_weather)
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    return render(request, "main_menu.html", {"dekt_data_list": data_list, "minhang_weather": weather[1:5]})


def shuiyuan(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "shuiyuan")
    thread = threading.Thread(target=process_shuiyuan, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_shuiyuan})
    thread.start()
    data_list = gpt_filter("shuiyuan_{}".format(jaccountname), lock=lock_shuiyuan)
    get_minhang_24h_weather(lock=lock_weather)
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    return render(request, "main_menu.html", {"shuiyuan_data_list": data_list, "minhang_weather": weather[1:5]})


def seiee(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "seiee")
    thread = threading.Thread(target=seiee_notification, kwargs={'lock': lock_seiee})
    thread.start()
    data_list = gpt_filter('seiee_notion', lock=lock_seiee)
    data_list = [data[1:] for data in data_list]
    get_minhang_24h_weather(lock=lock_weather)
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    return render(request, "main_menu.html", {"seiee_data_list": data_list, "minhang_weather": weather[1:5]})


def calendar(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "calendar")
    tablesid = transfer_from_database_to_list('tablesid_' + jaccountname)
    if request.method == "POST":
        lock_cookies.acquire()
        required_cookies = load_cookies(username='cookies_' + jaccountname + 'store')
        lock_cookies.release()
        schedule_type = request.POST.get('type')
        schedule_type_id = [table[2] for table in tablesid if table[1] == schedule_type][0]
        title = request.POST.get('title')
        start_date = request.POST.get('start-date')
        start_time = request.POST.get('start-time')
        end_date = request.POST.get('end-date')
        end_time = request.POST.get('end-time')
        location = request.POST.get('location')
        availability = request.POST.get('availability')
        reminder = int(request.POST.get('reminder'))
        description = request.POST.get('description')
        create_schedule(required_cookies, title, start_date + ' ' + start_time, end_date + ' ' + end_time, availability, reminderMinutes=reminder, allDay=False, location=location, description=description, schedule_type=schedule_type_id, recurrence=None)
        mysjtu_calendar(username=jaccountname,lock=lock_cookies,lock1=lock_calendar)
        return redirect("/calendar")

    thread = threading.Thread(target=mysjtu_calendar, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_calendar})
    thread.start()
    data_list = gpt_filter("calendar_{}".format(jaccountname), lock=lock_calendar)

    processed_data=[]
    for data in data_list:
        if data[6]=="false" or data[6]=="False":
            allday=False
        elif data[6]=="true" or data[6]=="True":
            allday=True
        processed_data.append({"id": data[5], "title": data[1] + " [" + data[4] + "]", "start": data[2], "end": data[3], "allDay": allday, 'url': "https://calendar.sjtu.edu.cn/ui/calendar"})
    json_data = json.dumps(processed_data)
    return render(request, "calendar.html", {"json_data": json_data,"tableid": [sublist[1] for sublist in tablesid if sublist[1] != '校历']})

def create__schedule(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    tablesid = transfer_from_database_to_list('tablesid_' + jaccountname)
    if request.method == "GET":
        return render(request, "create_schedule.html", {"tableid": [sublist[1] for sublist in tablesid if sublist[1] != '校历']})
    elif request.method == "POST":

        lock_cookies.acquire()
        required_cookies = load_cookies(username='cookies_' + jaccountname + 'store')
        lock_cookies.release()
        schedule_type = request.POST.get('type')
        schedule_type_id = [table[2] for table in tablesid if table[1] == schedule_type][0]
        title = request.POST.get('title')
        start_date = request.POST.get('start-date')
        start_time = request.POST.get('start-time')
        end_date = request.POST.get('end-date')
        end_time = request.POST.get('end-time')
        location = request.POST.get('location')
        availability = request.POST.get('availability')
        reminder = int(request.POST.get('reminder'))
        description = request.POST.get('description')
        create_schedule(required_cookies, title, start_date + ' ' + start_time, end_date + ' ' + end_time, availability, reminderMinutes=reminder, allDay=False, location=location, description=description, schedule_type=schedule_type_id, recurrence=None)
        return HttpResponse("Create done！！！！！！！！！！！！！！！！！！！")


def collection(request):
    # get_collection()

    shuiyuan_data_list = [[0, 'https://shuiyuan.sjtu.edu.cn/t/topic/167465', '100天诗词打卡(但是随机掉落猫猫)', 195, 70, False,
                           '宠物花草', "['坚持100天']", 1988],
                          [1, 'https://shuiyuan.sjtu.edu.cn/t/topic/207294', '不想上课不想上课不想上课不想上课', 23, 6, True,
                           '校园生活', "['发电']", 1043]]

    seiee_data_list = [['【素拓活动】【本科生综测】【1121项95分】第三届海洋装备发展战略论坛', '2023-10',
                        'https://www.seiee.sjtu.edu.cn/xsgz_tzgg_xssw_cat4/9184.html'],
                       ['【素拓活动】【本科生综测】【1121项95分】第三届海洋装备发展战略论坛', '2023-10',
                        'https://www.seiee.sjtu.edu.cn/xsgz_tzgg_xssw_cat4/9184.html']]
    dekt_data_list = [[0, '劳动教育',
                       'https://dekt.sjtu.edu.cn/h5/activities?categoryName=%E5%8A%B3%E5%8A%A8%E6%95%99%E8%82%B2&laborEducation=1',
                       '045d80d2-b469-4a5e-a4e1-7abdec8a4c12', '“机源动力”第四期——机械拆解学堂', '2023-10-20 19:00:00',
                       '2023-10-22 13:00:00', '2023-10-25 14:00:00', '2023-10-25 16:00:00',
                       'https://s3.jcloud.sjtu.edu.cn:443/2a9c49ee085a49b1907937307b539b06-arvato_uat/%E5%B0%81%E9%9D%A24_5wu1tGLN.png'],
                      [1, '劳动教育',
                       'https://dekt.sjtu.edu.cn/h5/activities?categoryName=%E5%8A%B3%E5%8A%A8%E6%95%99%E8%82%B2&laborEducation=1',
                       '61ab5323-6c46-4daf-b119-a53f345dc007', '行之有序|生科院非机动车停放引导劳动教育 2023秋 第七周',
                       '2023-10-18 21:00:00', '2023-10-22 21:00:00', '2023-10-23 08:30:00',
                       '2023-10-27 17:30:00',
                       'https://s3.jcloud.sjtu.edu.cn:443/2a9c49ee085a49b1907937307b539b06-arvato_uat/4fbee3327a850318081841e3d2b3904_eZnkgQPO.jpg']]

    get_minhang_24h_weather(lock=lock_weather)
    weather = gpt_filter("minhang_weather", lock=lock_weather)

    return render(request, "collection.html", {
        "shuiyuan_data_list": shuiyuan_data_list,
        "seiee_data_list": seiee_data_list,
        "dekt_data_list": dekt_data_list,
        "minhang_weather": weather[0:5],
    })


def add_to_favorites(request):
    if request.method == 'POST':
        collected_content = request.POST.dict()
        save_collection(collected_content.pop('site'), collected_content)
        return JsonResponse({'status': 'success'})
    else:
        print("gggggggggggggggggggg")
        return JsonResponse({'status': 'error'})
