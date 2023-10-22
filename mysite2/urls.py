"""
URL configuration for mysite2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app01 import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('mytest/',views.mytest),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    path('loginpage/', views.loginpage),
    path('logout/',views.log_out),
    path('show_canvas/', views.show_canvas),
    path('show_dekt/', views.show_dekt),
    path('show_shuiyuan/', views.show_shuiyuan),
    path('show_calendar/', views.show_calendar),
    path('sjtu_login/',views.sjtu_login),
    path('create_schedule/',views.create_schedule)
]
