from django.shortcuts import HttpResponse
from django.contrib import auth
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from combined import *
import threading
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.utils import timezone


# Create your views here.
def index(request):
    return render(request, "top.html")


def mainpage(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    zhihu_sample, bilibili_sample, weibo_sample, github_sample = get_today_regular()
    jaccountname = request.user.first_name
    if jaccountname == '':
        canvas_sample = dekt_sample = seiee_sample = shuiyuan_sample = '登录后显示'
        json_data=None
        tablesid=[]
    else:
        if request.method == "POST":
            lock_cookies.acquire()
            required_cookies = load_cookies(username='cookies_' + jaccountname + 'store')
            lock_cookies.release()
            lock_calendar.acquire()
            tablesid = transfer_from_database_to_list('tablesid_' + jaccountname)
            lock_calendar.release()
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
            mysjtu_calendar(username=jaccountname, lock=lock_cookies, lock1=lock_calendar)
            return redirect("/mainpage")
        mysjtu_calendar(username=jaccountname, lock=lock_cookies, lock1=lock_calendar)
        data_list = gpt_filter("calendar_{}".format(jaccountname), lock=lock_calendar)
        lock_calendar.acquire()
        tablesid = transfer_from_database_to_list('tablesid_' + jaccountname)
        lock_calendar.release()
        canvas_sample, dekt_sample, seiee_sample, shuiyuan_sample = get_today_SJTU(jaccountname)
        thread = threading.Thread(target=mysjtu_calendar, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_calendar})
        thread.start()
        processed_data = []
        for data in data_list:
            if data[6] == "false" or data[6] == "False":
                allday = False
            elif data[6] == "true" or data[6] == "True":
                allday = True
            processed_data.append({"id": data[5], "title": data[1] + " [" + data[4] + "]", "start": data[2], "end": data[3], "allDay": allday, 'url': "https://calendar.sjtu.edu.cn/ui/calendar"})
        json_data = json.dumps(processed_data)
    return render(request, "main_page.html", {'current_username':request.user.get_username(),'zhihu_sample': zhihu_sample, 'bilibili_sample': bilibili_sample, 'weibo_sample': weibo_sample, 'github_sample': github_sample, 'canvas_sample': canvas_sample, 'dekt_sample': dekt_sample, 'seiee_sample': seiee_sample, 'shuiyuan_sample': shuiyuan_sample,'json_data':json_data,"tableid": [sublist[1] for sublist in tablesid if sublist[1] != '校历']})


''' *********************** 定时任务 *********************** '''


def test_job():
    print("Update running!", strftime("%Y-%m-%d %H:%M:%S", localtime()))
    try:
        get_zhihu_hot_topic(lock=lock_zhihu,
                            cookie='_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410')
    except:
        print("get_zhihu_hot_topic FAILED")
    try:
        get_github_trending(lock=lock_github)
    except:
        print("get_github_trending FAILED")
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
trigger = IntervalTrigger(seconds=100)
scheduler.add_job(test_job, trigger=trigger, id="update_data")
scheduler.start()


def focustime(request):
    return render(request, "time.html")


def sjtu_login(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    if request.method == "GET":
        return render(request, "jaccount.html")
    jaccount_user = request.POST.get("signin_usr")
    jaccount_pwd = request.POST.get("signin_pwd")
    status, msg = validate_account(jaccount_user, jaccount_pwd)
    if not status:
        print("FAILED due to", msg)
        return render(request, "jaccount.html", {"errormsg": "用户名或者密码不正确"})  # 重定向到主页，后续添加错误信息
    request.user.first_name = jaccount_user
    request.user.save()
    check_box = request.POST.get('check_box')
    '''*******************数据库添加表单：request.user（当前使用SJTUhelper的用户）；jaccount_user（jaccount用户名）；cookies（暂空）*******************'''
    # thread4 = threading.Thread(target=mysjtu_calendar, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_calendar})
    # thread4.start()
    thread1 = threading.Thread(target=process_canvas, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_canvas})
    thread1.start()
    thread2 = threading.Thread(target=process_dekt, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_dekt})
    thread2.start()
    thread3 = threading.Thread(target=process_shuiyuan, kwargs={'username': jaccount_user, 'password': jaccount_pwd, 'lock': lock_cookies, 'lock1': lock_shuiyuan})
    thread3.start()

    return redirect("/mainpage")  # 重定向到主页


def show_calendar(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
    print(request.user, "|", jaccountname, "|", "calendar")
    thread = threading.Thread(target=mysjtu_calendar, kwargs={"username": jaccountname, 'lock': lock_cookies, 'lock1': lock_calendar})
    thread.start()
    data_list = gpt_filter(site="calendar_" + jaccountname, lock=lock_calendar, mode=1)
    schedule_data_json = []
    for schedule in data_list:
        schedule_data_json.append([schedule[1] + "[" + schedule[4] + "]", schedule[2], schedule[3], schedule[5], schedule[6]])
    print("json data to be used:", json.dumps(schedule_data_json))
    return render(request, "show_calendar.html", {"calendar_data_list": data_list})


def log_out(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname != '':
        erase_SJTU_user(jaccountname)
    request.user.first_name=''
    request.user.save()
    auth.logout(request)
    return redirect("/")


def send(request):
    if request.method == 'POST':

        # current_site = get_current_site(request)
        # 发送激活邮件
        username = request.POST.get('username')
        email = request.POST.get('email')
        user = User.objects.filter(username=username, email=email)
        if not user:
            return JsonResponse({'message': '不存在此用户，请检查用户名或者邮箱'}, status=400)
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
            send_mail(mail_subject, f'这是你的邮箱验证码:' + token + '\n有效时间为5分钟', 'sjtuhelper@163.com', [email])

            return JsonResponse({'message': '邮箱验证码已发送,有限时间5分钟'})
        except:
            return JsonResponse({'message': '无效的请求方法,请检查邮箱是否格式正确'})
    else:
        return JsonResponse({'message': '无效的请求方法'}, status=400)


def loginpage(request):
    if request.method == "GET":
        return render(request, "sign.html")
    else:
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
                # thread6 = threading.Thread(target=get_minhang_24h_weather, kwargs={'lock': lock_weather})
                # thread6.start()
                return redirect("/mainpage")

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
                print(request.session.get('verification_token'), token)
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
    username = request.POST.get("username")
    email = request.POST.get('email')
    token = request.POST.get('token')
    password = request.POST.get('password')
    user = User.objects.filter(username=username, email=email)
    if not user:
        return JsonResponse({'message': '不存在此用户，请检查用户名或者邮箱'}, status=400)
    user = user.first()
    user.set_password(password)
    user.is_active = True
    print(request.session.get('verification_token'))
    if token != request.session.get('verification_token'):
        return JsonResponse({'message': '验证码错误'}, status=400)
    if request.session.get('verification_expiry') < timezone.now().isoformat():
        return JsonResponse({'message': '验证码超时'}, status=400)
    user.save()
    return JsonResponse({'message': '修改成功'})


def send_signup(request):
    if request.method == 'POST':

        # current_site = get_current_site(request)
        # 发送激活邮件
        username = request.POST.get('username')
        pwd = request.POST.get("signup_pwd")
        repwd = request.POST.get("signup_repwd")
        email = request.POST.get('email')
        if not (username and pwd and repwd and email):
            return JsonResponse({'message': '输入不允许有空值'}, status=400)
        user = User.objects.filter(username=username)
        if user:
            return JsonResponse({'message': '用户已经存在，尝试别的用户名'}, status=400)
        if pwd != repwd:
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
            send_mail(mail_subject, '这是你的邮箱验证码:' + token + '\n有效时间为5分钟', 'sjtuhelper@163.com', [email])
            return JsonResponse({'message': '邮箱验证码已发送,有效时间5分钟'})
        except:
            return JsonResponse({'message': '无效的请求方法,请检查邮箱是否格式正确'}, status=400)


    else:
        return JsonResponse({'message': '无效的请求方法'}, status=400)


def zhihu(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    if request.method == "GET":
        thread = threading.Thread(target=get_zhihu_hot_topic, kwargs={'lock': lock_zhihu,
                                                                      'cookie': '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'})
        thread.start()
        reducedHotTopics1 = gpt_filter('zhihu', lock=lock_zhihu, mode=1)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        zhihukeywords = getkeyword(request.user, 'zhihu', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"zhihuHotTopic": reducedHotTopics1, "minhang_weather": weather[1:5], "key": zhihukeywords})
    else:
        keys = ""
        setkeys = []
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys == '':
            mode = 1
        else:
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'zhihu', True, setkeys)

        reducedHotTopics = gpt_filter('zhihu', cue=keys, lock=lock_zhihu, mode=mode)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        zhihukeywords = getkeyword(request.user, 'zhihu', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"zhihuHotTopic": reducedHotTopics, "key": zhihukeywords, "minhang_weather": weather[1:5]})


def github(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    if request.method == "GET":
        thread = threading.Thread(target=get_github_trending, kwargs={'lock': lock_github})
        thread.start()
        reducedHotTopics = gpt_filter('github', lock=lock_github, mode=1)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        githubkeywords = getkeyword(request.user, 'github', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"key": githubkeywords,
                                                  "github": reducedHotTopics,
                                                  "minhang_weather": weather[1:5]})
    else:
        keys = ""
        setkeys = []
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys == '':
            mode = 1
        else:
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'github', True, setkeys)
        reducedHotTopics = gpt_filter('github', cue=keys, lock=lock_github, mode=mode)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        githubkeywords = getkeyword(request.user, 'github', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"github": reducedHotTopics, "key": githubkeywords, "minhang_weather": weather[1:5]})


def bilibili(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    if (request.method == "GET"):
        thread = threading.Thread(target=get_bilibili_ranking, kwargs={'lock': lock_bilibili})
        thread.start()
        reducedHotTopics3 = gpt_filter('bilibili', lock=lock_bilibili, mode=1)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        bilibilikeywords = getkeyword(request.user, 'bilibili', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"key": bilibilikeywords,
                                                  "bilibili": reducedHotTopics3,
                                                  "minhang_weather": weather[1:5]
                                                  })
    else:
        keys = ""
        setkeys = []
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys == '':
            mode = 1
        else:
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'bilibili', True, setkeys)

        reducedHotTopics = gpt_filter('bilibili', cue=keys, lock=lock_bilibili, mode=mode)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        bilibilikeywords = getkeyword(request.user, 'bilibili', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"bilibili": reducedHotTopics, "key": bilibilikeywords, "minhang_weather": weather[1:5]})


def weibo(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    if request.method == "GET":
        thread = threading.Thread(target=get_weibo_hot_topic, kwargs={'lock': lock_weibo})
        thread.start()
        reducedHotTopics4 = gpt_filter('weibo', lock=lock_weibo, mode=1)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        weibokeywords = getkeyword(request.user, 'weibo', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"weibo": reducedHotTopics4, "key": weibokeywords, "minhang_weather": weather[1:5]})
    else:
        keys = ""
        setkeys = []
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys == '':
            mode = 1
        else:
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'weibo', True, setkeys)

        reducedHotTopics = gpt_filter('weibo', cue=keys, lock=lock_weibo, mode=mode)
        weather = gpt_filter("minhang_weather", lock=lock_weather)
        weibokeywords = getkeyword(request.user, 'weibo', False)
        return render(request, "main_menu.html", {'current_username':request.user.get_username(),"weibo": reducedHotTopics, "key": weibokeywords, "minhang_weather": weather[1:5]})


def canvas(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
    print(request.user, "|", jaccountname, "|", "canvas")
    thread = threading.Thread(target=process_canvas, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_canvas})
    thread.start()

    mode = 1
    keys = ""
    setkeys = []
    if request.method == "POST":
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys != '':
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'canvas', True, setkeys)

    data_list = gpt_filter("canvas_{}".format(jaccountname), lock=lock_canvas, cue=keys, mode=mode)
    for item in data_list:
        item[5] = mark_safe(item[5])
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    canvaskeywords = getkeyword(request.user, 'canvas', False)
    return render(request, "main_menu.html", {'current_username':request.user.get_username(),"canvas_data_list": data_list, "minhang_weather": weather[1:5], 'key': canvaskeywords})


def dekt(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
    print(request.user, "|", jaccountname, "|", "dekt")
    # thread = threading.Thread(target=process_dekt, kwargs={"username": jaccountname, 'lock': lock_cookies, 'lock1': lock_dekt})
    # thread.start()

    mode = 1
    keys = ""
    setkeys = []
    if request.method == "POST":
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys != '':
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'dekt', True, setkeys)

    data_list = gpt_filter("dekt", cue=keys, mode=mode, lock=lock_dekt)
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    dektkeywords = getkeyword(request.user, 'dekt', False)
    return render(request, "main_menu.html", {'current_username':request.user.get_username(),"dekt_data_list": data_list, "minhang_weather": weather[1:5], 'key': dektkeywords})


def shuiyuan(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
    print(request.user, "|", jaccountname, "|", "shuiyuan")
    thread = threading.Thread(target=process_shuiyuan, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_shuiyuan})
    thread.start()
    mode = 1
    keys = ""
    setkeys = []
    if request.method == "POST":
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys != '':
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'shuiyuan', True, setkeys)
    data_list = gpt_filter("shuiyuan_{}".format(jaccountname), lock=lock_shuiyuan, cue=keys, mode=mode)
    data_list = [list(data) for data in data_list]
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    shuiyuankeywords = getkeyword(request.user, 'shuiyuan', False)
    return render(request, "main_menu.html", {'current_username':request.user.get_username(),"shuiyuan_data_list": data_list, "minhang_weather": weather[1:5],'key':shuiyuankeywords})


def seiee(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
    print(request.user, "|", jaccountname, "|", "seiee")
    thread = threading.Thread(target=seiee_notification, kwargs={'lock': lock_seiee})
    thread.start()
    mode = 1
    keys = ""
    setkeys = []
    if request.method == "POST":
        for i in range(5):
            key_place = request.POST.getlist("key-" + str(i + 1))
            if key_place is None:
                continue
            for key in key_place:
                keys += key + '或者'
                setkeys.append(key)
        if keys != '':
            mode = None
            keys = keys[:-2]
            getkeyword(request.user, 'seiee', True, setkeys)

    data_list = gpt_filter('seiee_notion', cue=keys, mode=mode, lock=lock_seiee)
    data_list = [list(data[1:]) for data in data_list]
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    seieekeywords = getkeyword(request.user, 'seiee', False)
    return render(request, "main_menu.html", {'current_username':request.user.get_username(),"seiee_data_list": data_list, "minhang_weather": weather[1:5],'key':seieekeywords})


def calendar(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
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
        mysjtu_calendar(username=jaccountname, lock=lock_cookies, lock1=lock_calendar)
        return redirect("/calendar")

    data_list = gpt_filter("calendar_{}".format(jaccountname), lock=lock_calendar)
    thread = threading.Thread(target=mysjtu_calendar, kwargs={'username': jaccountname, 'lock': lock_cookies, 'lock1': lock_calendar})
    thread.start()
    processed_data = []
    for data in data_list:
        if data[6] == "false" or data[6] == "False":
            allday = False
        elif data[6] == "true" or data[6] == "True":
            allday = True
        processed_data.append({"id": data[5], "title": data[1] + " [" + data[4] + "]", "start": data[2], "end": data[3], "allDay": allday, 'url': "https://calendar.sjtu.edu.cn/ui/calendar"})
    json_data = json.dumps(processed_data)
    return render(request, "calendar.html", {"json_data": json_data, "tableid": [sublist[1] for sublist in tablesid if sublist[1] != '校历']})


def create__schedule(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    jaccountname = request.user.first_name
    if jaccountname == '':
        return redirect("/sjtu_login")
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


def show_collection(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    a = collection.objects.filter(user=request.user).values()
    collected_data = {'zhihu': [], 'github': [], 'bilibili': [], 'weibo': [], 'shuiyuan': [], 'canvas': [], 'dekt': [], 'seiee': [], 'calendar': []}
    for item in a:
        item.pop('user')
        site = item.pop('site')
        solid_data = []
        for x in list(item.values())[1:]:
            if x is not None:
                solid_data.append(x)
        collected_data[site].append(solid_data)
    for weibo in collected_data['weibo']:
        weibo[1] = 'img/weibo_default_pic.jpg'
    weather = gpt_filter("minhang_weather", lock=lock_weather)
    return render(request, "collection.html", {"zhihuHotTopic": collected_data['zhihu'], "github": collected_data['github'], "bilibili": collected_data['bilibili'], "weibo": collected_data['weibo'], "canvas_data_list": collected_data['canvas'],
                                               "shuiyuan_data_list": collected_data['shuiyuan'],
                                               "seiee_data_list": collected_data['seiee'],
                                               "dekt_data_list": collected_data['dekt'],
                                               "minhang_weather": weather[0:5],
                                               })


def process_favorites(request):
    if not request.user.is_authenticated:
        return redirect("/loginpage")
    if request.method == 'POST':
        collected_content = request.POST.dict()
        if collected_content.pop('status') == "btn-uncollected":
            save_collection(request.user, collected_content.pop('site'), collected_content)
        else:
            delete_collection(request.user, collected_content.pop('site'), collected_content)
        return JsonResponse({'status': 'success'})
    else:
        redirect("/mainpage")
