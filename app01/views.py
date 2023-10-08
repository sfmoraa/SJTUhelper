from django.shortcuts import render, HttpResponse, redirect
from app01.models import *

print("views running")
from combined import *
import pandas as pd

# Create your views here.
def index(request):
    return HttpResponse("欢迎使用")


def top(request):
    reducedHotTopics = gpt_filter('zhihu')
    return render(request, "top.html", {"zhihuHotTopic": reducedHotTopics})
def user_list(request):
    # return HttpResponse("用户列表")
    return render(request, "user_list.html")


def user_add(request):
    return HttpResponse("添加用户")
    # return render(request, "user_add.html")


def mytest(request):
    # get_zhihu_hot_topic(cookie = '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410')
    # get_github_trending()
    # get_bilibili_ranking()
    # get_weibo_hot_topic()
    # dekt()
    # shuiyuan()
    # mysjtu_calendar()
    # get_minhang_24h_weather()
    # reducedHotTopics1 = gpt_filter('zhihu',cue="我对军事政治不感兴趣")
    # reducedHotTopics2 = gpt_filter('github',cue=None)
    # reducedHotTopics3 = gpt_filter('bilibili',cue="我想获得小于10条内容")
    # reducedHotTopics4 = gpt_filter('weibo')
    # reducedHotTopics5 = gpt_filter('shuiyuan_zt-785')
    # reducedHotTopics6 = gpt_filter('calendar_zt-785')
    # reducedHotTopics7 = gpt_filter("dekt",cue=None)
    # reducedHotTopics8 = gpt_filter("seiee_notion")
    reducedHotTopics9 = gpt_filter("minhang_weather")
    reducedHotTopics1 = []
    reducedHotTopics2 = []
    reducedHotTopics3 = []
    reducedHotTopics4 = []
    reducedHotTopics5 = []
    reducedHotTopics6 = []
    reducedHotTopics7 = []
    reducedHotTopics8 = []
    # reducedHotTopics9 = []
    return render(request, "mytest.html", {"zhihuHotTopic": reducedHotTopics1,"github":reducedHotTopics2,"bilibili":reducedHotTopics3,"weibo":reducedHotTopics4,"shuiyuan":reducedHotTopics5,"calendar":reducedHotTopics6,"dekt":reducedHotTopics7,"seiee_notion":reducedHotTopics8,"minhang_weather":reducedHotTopics9})


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


def login(request):
    if request.method == "GET":
        return render(request, "login.html")
    else:
        # print(request.POST)
        username = request.POST.get("user")
        password = request.POST.get("pwd")
        user = UserInfo.objects.filter(name=username, password=password).first()
        if user:
            # 用户名和密码匹配，执行登录成功的逻辑
            # 例如，可以设置用户登录状态或重定向到其他页面
            # return HttpResponse("登录成功")
            return redirect("https://www.sjtu.edu.cn")
        else:
            # 用户名或密码不正确，返回登录页面并显示错误信息
            return render(request, 'login.html', {'error_message': '用户名或密码不正确'})



def orm(request):
    Department.objects.create(title="销售部")
    Department.objects.create(title="财务部")
    Department.objects.create(title="人力资源部")

    Department.objects.filter(id=10).delete()

    UserInfo.objects.create(name="武沛齐", password="123", age=19)
    UserInfo.objects.create(name="朱虎飞", password="666", age=29)
    UserInfo.objects.create(name="吴阳军", password="666", age=20)

    return HttpResponse("修改成功")


def info_list(request):
    data_list = UserInfo.objects.all()
    print(data_list)
    return render(request, "info_list.html", {"data_list": data_list})


def info_add(request):
    if request.method == "GET":
        return render(request, "info_add.html")
    user = request.POST.get("user")
    pwd = request.POST.get("pwd")
    age = request.POST.get("age")
    UserInfo.objects.create(name=user, password=pwd, age=age)
    create_dynamic_model_collection(table_name=user.rstrip("\n"))
    # return HttpResponse("添加成功")
    return redirect("http://127.0.0.1:8000/info/list/")


def info_delete(request):
    nid = request.GET.get("nid")
    # delete_dynamic_model_collection(UserInfo.objects.filter(id=nid).first().name)
    UserInfo.objects.filter(id=nid).delete()
    # return HttpResponse("删除成功")
    return redirect("http://127.0.0.1:8000/info/list/")
