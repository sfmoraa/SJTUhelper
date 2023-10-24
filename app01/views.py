import time

import requests
from django.shortcuts import render, HttpResponse, redirect
from app01.models import *
from django.contrib.auth.models import User
from django.contrib import auth
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

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
        get_zhihu_hot_topic(lock=lock_zhihu,cookie='_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410')
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
        return render(request, "sjtu_login.html")
    jaccount_user = request.POST.get("user")
    jaccount_pwd = request.POST.get("pwd")
    status, msg = validate_account(jaccount_user, jaccount_pwd)
    if not status:
        print("FAILED due to", msg)
        return redirect("http://127.0.0.1:8000/sjtu_login/")  # 重定向到主页，后续添加错误信息
    request.user.first_name = jaccount_user
    request.user.save()
    check_box = request.POST.get('check_box')
    '''*******************数据库添加表单：request.user（当前使用SJTUhelper的用户）；jaccount_user（jaccount用户名）；cookies（暂空）*******************'''
    thread1 = threading.Thread(target=canvas, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_canvas})
    thread1.start()
    thread2 = threading.Thread(target=dekt, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_dekt})
    thread2.start()
    thread3 = threading.Thread(target=shuiyuan, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_shuiyuan})
    thread3.start()
    thread4 = threading.Thread(target=mysjtu_calendar, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_calendar})
    thread4.start()
    return redirect("http://127.0.0.1:8000/sjtu_login/")  # 重定向到主页


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


def show_canvas(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname is None:
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "canvas")
    thread = threading.Thread(target=canvas, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_canvas})
    thread.start()
    data_list = gpt_filter("canvas_{}".format(jaccountname), lock=lock_canvas)
    # 读取该用户canvas信息，下为样例数据，需转为从数据库调取。注意！！！：下数据为从csv文件读取而来，第一项编号可能没有
    # data_list = [[0, '/', 'Not required', 135243, '数字信号处理（E）', '/', '请尽快加入课程通知群', 'https://oc.sjtu.edu.cn/courses/59766/discussion_topics/135243'],
    #              [2, '2023-10-11+23:59:59', 'true', 248811, '安全开发模型及安全编程', '<p>提交需求规划和项目进度计划，每组提交一份。</p>\r\n<p>具体要求：</p>\r\n<p>1、需求规划：一张思维导图，要体现出Epic，Feature，Story, Task四个层次的需求规划。</p>\r\n<p>2、项目进度计划：可以用Excell表格或甘特图，需要体现出开发任务的人员分工和时间进度计划。</p>\r\n<p>\xa0</p>', '项目计划提交',
    #               'https://oc.sjtu.edu.cn/courses/59762/assignments/248811']]
    return render(request, "show_canvas.html", {"canvas_data_list": data_list})


def show_dekt(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "dekt")
    thread = threading.Thread(target=dekt, kwargs={"username": jaccountname, 'lock': lock_cookies, 'lock1': lock_dekt})
    thread.start()
    data_list = gpt_filter("dekt", cue=None, mode=1, lock=lock_dekt)
    # 读取该用户dekt信息，下为样例数据，需转为从数据库调取。注意！！！：下数据为从csv文件读取而来，第一项编号可能没有
    # data_list = [[0, '劳动教育', 'https://dekt.sjtu.edu.cn/h5/activities?categoryName=%E5%8A%B3%E5%8A%A8%E6%95%99%E8%82%B2&laborEducation=1', '045d80d2-b469-4a5e-a4e1-7abdec8a4c12', '“机源动力”第四期——机械拆解学堂', '2023-10-20 19:00:00', '2023-10-22 13:00:00', '2023-10-25 14:00:00', '2023-10-25 16:00:00',
    #               'https://s3.jcloud.sjtu.edu.cn:443/2a9c49ee085a49b1907937307b539b06-arvato_uat/%E5%B0%81%E9%9D%A24_5wu1tGLN.png'],
    #              [1, '劳动教育', 'https://dekt.sjtu.edu.cn/h5/activities?categoryName=%E5%8A%B3%E5%8A%A8%E6%95%99%E8%82%B2&laborEducation=1', '61ab5323-6c46-4daf-b119-a53f345dc007', '行之有序|生科院非机动车停放引导劳动教育 2023秋 第七周', '2023-10-18 21:00:00', '2023-10-22 21:00:00', '2023-10-23 08:30:00',
    #               '2023-10-27 17:30:00', 'https://s3.jcloud.sjtu.edu.cn:443/2a9c49ee085a49b1907937307b539b06-arvato_uat/4fbee3327a850318081841e3d2b3904_eZnkgQPO.jpg']]
    return render(request, "show_dekt.html", {"dekt_data_list": data_list})


def show_shuiyuan(request):
    if not request.user.is_authenticated:
        return redirect("http://127.0.0.1:8000/loginpage/")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(request.user, "|", jaccountname, "|", "shuiyuan")
    if jaccountname == '':
        return HttpResponse("未登录！！！！！！！！！！！！！！！！！！！")
    print(jaccountname)
    thread = threading.Thread(target=shuiyuan, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_shuiyuan})
    thread.start()

    data_list = gpt_filter("shuiyuan_{}".format(jaccountname), lock=lock_shuiyuan)
    # 读取该用户水源信息，下为样例数据，需转为从数据库调取。注意！！！：下数据为从csv文件读取而来，第一项编号可能没有
    # data_list = [[0, 'https://shuiyuan.sjtu.edu.cn/t/topic/167465', '100天诗词打卡(但是随机掉落猫猫)', 195, 70, False, '宠物花草', "['坚持100天']", 1988], [1, 'https://shuiyuan.sjtu.edu.cn/t/topic/207294', '不想上课不想上课不想上课不想上课', 23, 6, True, '校园生活', "['发电']", 1043]]
    return render(request, "show_shuiyuan.html", {"shuiyuan_data_list": data_list})


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


def send(request, user, email):
    current_site = get_current_site(request)
    # 发送激活邮件
    mail_subject = '激活您的账号'
    activation_link = f"http://{current_site.domain}/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/"
    message = render_to_string('activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })
    send_mail(mail_subject, message, 'sjtuhelper@163.com', [email])


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
        if 'signup' in request.POST:
            username = request.POST.get("signup_usr")
            pwd = request.POST.get("signup_pwd")
            repwd = request.POST.get("signup_repwd")
            email = request.POST.get("email")

            if User.objects.filter(username=username):
                return render(request, "sign.html", {'error1': '用户名重复'})
            if pwd != repwd:
                return render(request, "sign.html", {'error2': "两次密码不一致"})
            user = User(username=username, email=email)
            user.set_password(pwd)
            user.is_active = False  # 设置用户状态为未激活
            user.save()
            send(request, user, email)
            return HttpResponse('请点击邮箱链接验证')
