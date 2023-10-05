from django.db import models

print("models running")
# Create your models here.
class UserInfo(models.Model):
    name = models.CharField(max_length=32)
    password = models.CharField(max_length=64)
    age = models.IntegerField(default=20)

class Department(models.Model):
    title = models.CharField(max_length=16)

class Role(models.Model):
    caption = models.CharField(max_length=16)


class users(models.Model):
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=50)
    created_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '用户表'
        verbose_name_plural = verbose_name
