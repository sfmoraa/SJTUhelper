from django.shortcuts import render, HttpResponse, redirect
from app01.models import Department, UserInfo

print("views running")
from combined import *
import pandas as pd


# Create your views here.
def index(request):
    return HttpResponse("欢迎使用")


def user_list(request):
    # return HttpResponse("用户列表")
    return render(request, "user_list.html")


def user_add(request):
    return HttpResponse("添加用户")
    # return render(request, "user_add.html")


def mytest(request):
    reducedHotTopics = gpt_filter('zhihu', cue="")
    return render(request, "mytest.html", {"zhihuHotTopic": reducedHotTopics})


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

        if username == "root" and password == "admin":
            # return HttpResponse("登录成功")
            return redirect("https://www.sjtu.edu.cn")
        else:
            # return HttpResponse("登录失败")
            return render(request, "login.html", {"error_msg": "用户名或密码错误"})


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
    # return HttpResponse("添加成功")
    return redirect("http://127.0.0.1:8000/info/list/")


def info_delete(request):
    nid = request.GET.get("nid")
    UserInfo.objects.filter(id=nid).delete()
    # return HttpResponse("删除成功")
    return redirect("http://127.0.0.1:8000/info/list/")


def main(request):
    if request.method == "GET":
        reducedHotTopics = gpt_filter('zhihu', cue="")
        return render(request, "main.html",
                      {"zhihuHotTopic": reducedHotTopics, "key": "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"})
    else:
        key = request.POST.get("key")
        print(key)

        reducedHotTopics = gpt_filter('zhihu', cue=key)
        return render(request, "main.html", {"zhihuHotTopic": reducedHotTopics, "key": key})

