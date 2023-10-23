# SJTUhelper
A helpful website that helps SJTU students easily access trending information and campus-related updates.



在app01/migrations文件夹下只有init.py时执行以下命令（如果有其他py文件可以删除掉

```
python manage.py makemigrations
python manage.py migrate
```

SJTU板块需要到官网上下载pytesseract，并且添加相关环境变量。

在终端过``python manage.py createsuperuser`` 创建超级用户也就是管理员，可以通过admin/查看所有用户、组以及数据库的内容。

邮箱需要在setting.py最下面的几行添加自己的邮箱设置。
