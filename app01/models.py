from django.db import models, OperationalError
import pymysql
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

print("models running")


class zhihu(models.Model):
    number = models.CharField(max_length=10, default='')
    title = models.CharField(max_length=500, default='')
    href = models.CharField(max_length=500, default='')
    picture_element = models.URLField(max_length=1000, default='')


class github(models.Model):
    author = models.CharField(max_length=20)
    title = models.CharField(max_length=500)
    description = models.CharField(max_length=500)
    href = models.URLField(max_length=500)


class bilibili(models.Model):
    rank = models.IntegerField(default=1)
    pic_href = models.CharField(max_length=500, default='')
    title = models.CharField(max_length=500, default='')
    tname = models.CharField(max_length=100, default='')
    link = models.URLField(max_length=500, default='')


class weibo(models.Model):
    rank_pic_href = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=10000)


class dektinfo(models.Model):
    category = models.CharField(max_length=100)
    category_url = models.TextField(default="https://dekt.sjtu.edu.cn/h5/index")
    item_id = models.CharField(max_length=100)
    activity_name = models.CharField(max_length=100)
    enroll_start_time = models.CharField(max_length=100)
    enroll_end_time = models.CharField(max_length=100)
    active_start_time = models.CharField(max_length=100)
    active_end_time = models.CharField(max_length=100)
    activity_picurl = models.TextField()

    def __str__(self):
        return self.activity_name


class seieeNotification(models.Model):
    name = models.CharField(max_length=100)
    date = models.CharField(max_length=100)
    href = models.URLField(max_length=100)


class minhang_24h_weather(models.Model):
    Name_of_weather_picture = models.CharField(max_length=100)
    weather_text = models.CharField(max_length=100)
    temperature = models.CharField(max_length=100)
    wind_direction = models.CharField(max_length=100)
    wind_strength = models.CharField(max_length=100)
    hour = models.CharField(max_length=100)


class collection(models.Model):
    user = models.CharField(default="admin",max_length=100)
    site = models.CharField(max_length=100)
    data0 = models.TextField(null=True, blank=True)
    data1 = models.TextField(null=True, blank=True)
    data2 = models.TextField(null=True, blank=True)
    data3 = models.TextField(null=True, blank=True)
    data4 = models.TextField(null=True, blank=True)
    data5 = models.TextField(null=True, blank=True)
    data6 = models.TextField(null=True, blank=True)
    data7 = models.TextField(null=True, blank=True)
    data8 = models.TextField(null=True, blank=True)
    data9 = models.TextField(null=True, blank=True)
    data10 = models.TextField(null=True, blank=True)


def create_dynamic_model_collection(table_name):
    table_name = 'collection_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 创建表格
    create_table_query = """
        CREATE TABLE `{}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            source VARCHAR(100),
            title VARCHAR(100),
            image_url VARCHAR(200),
            link_url VARCHAR(200)
        )
        """.format(table_name)
    cursor.execute(create_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def delete_dynamic_model_collection(table_name):
    table_name = 'collection_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    # 执行 SQL 语句
    drop_table_query = "DROP TABLE IF EXISTS " + "`{}`".format(table_name) + ";"
    cursor.execute(drop_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def insert_dynamic_model_collection(table_name, source, title, image_url, link_url):
    # 打开数据库连接
    table_name = 'collection_' + table_name
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    insert_data_query = """
        INSERT INTO `{}` (source, title, image_url, link_url)
        VALUES
            ('{}', '{}', '{}', '{}');
        """.format(table_name, source, title, image_url, link_url)
    cursor.execute(insert_data_query)
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def create_dynamic_model_shuiyuan(table_name):
    table_name = 'shuiyuan_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 创建表格
    create_table_query = """
        CREATE TABLE IF NOT EXISTS `{}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            `ref` VARCHAR(100),
            `title` VARCHAR(100),
            `posts_count` VARCHAR(100),
            `reply_count` VARCHAR(100),
            `unseen` VARCHAR(100),
            `shuiyuan_category_dict` VARCHAR(100),
            `tags` VARCHAR(100),
            `views` VARCHAR(100)
        )
        """.format(table_name)
    cursor.execute(create_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def delete_dynamic_model_shuiyuan(table_name):
    table_name = 'shuiyuan_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    # 执行 SQL 语句
    drop_table_query = "DROP TABLE IF EXISTS " + "`{}`".format(table_name) + ";"
    cursor.execute(drop_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def insert_dynamic_model_shuiyuan(table_name, ref, title, posts_count, reply_count, unseen, shuiyuan_category_dict, tags, views):
    # 打开数据库连接
    table_name = 'shuiyuan_' + table_name
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    insert_data_query = """
        INSERT INTO `{}` (`ref`, `title`, `posts_count`, `reply_count`, `unseen`, `shuiyuan_category_dict`, `tags`, `views`)
        VALUES
            ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');
        """.format(table_name, ref, title, posts_count, reply_count, unseen, shuiyuan_category_dict, tags, views)
    cursor.execute(insert_data_query)
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def create_dynamic_model_calendar(table_name):
    table_name = 'calendar_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 创建表格
    create_table_query = """
        CREATE TABLE IF NOT EXISTS `{}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(100),
            starttime VARCHAR(100),
            endtime VARCHAR(100),
            location VARCHAR(100),
            json_detail_url VARCHAR(100),
            allday VARCHAR(10)
        )
        """.format(table_name)
    cursor.execute(create_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def delete_dynamic_model_calendar(table_name):
    table_name = 'calendar_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    # 执行 SQL 语句
    drop_table_query = "DROP TABLE IF EXISTS " + "`{}`".format(table_name) + ";"

    cursor.execute(drop_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def insert_dynamic_model_calendar(table_name, title, starttime, endtime, location, json_detail_url, allday):
    # 打开数据库连接
    table_name = 'calendar_' + table_name
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    insert_data_query = """
        INSERT INTO `{}` (title, starttime, endtime, location, json_detail_url, allday)
        VALUES
            ('{}', '{}', '{}', '{}', '{}', '{}');
        """.format(table_name, title, starttime, endtime, location, json_detail_url, allday)
    cursor.execute(insert_data_query)
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def create_dynamic_model_canvas(table_name):
    table_name = 'canvas_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 创建表格
    create_table_query = """
        CREATE TABLE IF NOT EXISTS `{}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            due_at VARCHAR(100),
            submit VARCHAR(100),
            plannable_id VARCHAR(100),
            course_id_name_dict VARCHAR(100),
            descript TEXT,
            _name VARCHAR(100),
            html_url VARCHAR(100)
        )
        """.format(table_name)

    cursor.execute(create_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def delete_dynamic_model_canvas(table_name):
    table_name = 'canvas_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    # 执行 SQL 语句
    drop_table_query = "DROP TABLE IF EXISTS " + "`{}`".format(table_name) + ";"

    cursor.execute(drop_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def insert_dynamic_model_canvas(table_name, due_at, submit, plannable_id, course_id_name_dict, descript, _name, html_url):
    # 打开数据库连接
    table_name = 'canvas_' + table_name
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    insert_data_query = """
        INSERT INTO `{}` (due_at, submit, plannable_id, course_id_name_dict, descript, _name, html_url)
        VALUES
            ('{}', '{}', '{}', '{}', '{}', '{}', '{}');
        """.format(table_name, due_at, submit, plannable_id, course_id_name_dict, descript, _name, html_url)

    cursor.execute(insert_data_query)
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def create_dynamic_model_cookies(table_name):
    table_name = 'cookies_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 创建表格
    create_table_query = """
        CREATE TABLE IF NOT EXISTS `{}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100),
            value TEXT,
            domain VARCHAR(100),
            path VARCHAR(100),
            secure VARCHAR(10)
        )
        """.format(table_name)

    cursor.execute(create_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def delete_dynamic_model(table_name):
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    # 执行 SQL 语句
    drop_table_query = "DROP TABLE IF EXISTS " + "`{}`".format(table_name) + ";"

    cursor.execute(drop_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def insert_dynamic_model_cookies(table_name, name, value, domain, path, secure):
    # 打开数据库连接
    table_name = 'cookies_' + table_name
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    insert_data_query = """
        INSERT INTO `{}` (name, value, domain, path, secure)
        VALUES
            ('{}', '{}', '{}', '{}', '{}');
        """.format(table_name, name, value, domain, path, secure)

    cursor.execute(insert_data_query)
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def transfer_from_database_to_list(tablename):
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    sql = "select * from `{}`".format(tablename)
    cursor.execute(sql)
    content = []
    if 'canvas' not in tablename:
        while True:
            row = cursor.fetchone()
            if not row:
                break
            content.append(row)
        return content
    else:
        while True:
            row = cursor.fetchone()
            if not row:
                break
            fifth_element = row[5]  # 获取第五个元素
            safe_fifth_element = mark_safe(fifth_element)  # 对第五个元素应用mark_safe函数
            row = list(row)  # 将元组转换为列表，以便修改第五个元素
            row[5] = safe_fifth_element  # 更新第五个元素为安全的HTML
            content.append(row)
        return content


def create_dynamic_model_tablesid(table_name):
    table_name = 'tablesid_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 创建表格
    create_table_query = """
        CREATE TABLE IF NOT EXISTS `{}` (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100),
            value TEXT
        )
        """.format(table_name)

    cursor.execute(create_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def delete_dynamic_model_tablesid(table_name):
    table_name = 'tablesid_' + table_name
    # 打开数据库连接
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    # 执行 SQL 语句
    drop_table_query = "DROP TABLE IF EXISTS " + "`{}`".format(table_name) + ";"

    cursor.execute(drop_table_query)
    # 提交事务
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()


def insert_dynamic_model_tablesid(table_name, name, value):
    # 打开数据库连接
    table_name = 'tablesid_' + table_name
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    insert_data_query = """
        INSERT INTO `{}` (name, value)
        VALUES
            ('{}', '{}');
        """.format(table_name, name, value)

    cursor.execute(insert_data_query)
    db.commit()
    # 关闭游标和数据库连接
    cursor.close()
    db.close()
