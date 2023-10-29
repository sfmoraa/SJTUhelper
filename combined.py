import random
import requests
import openai
import pandas as pd
import re
from lxml import etree
from time import time, localtime, strftime, mktime, strptime
from PIL import Image, ImageEnhance
import pytesseract
import shutil
import json
import os
import http.cookiejar
from app01.models import *
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
lock_keywords = threading.Lock()

openai.api_key = "sk-NzVkxZUYP9aHqeUbkSxAGvfUgn5vzsPKANnG1UHR3YMa1XLp"
openai.api_base = "https://api.chatanywhere.com.cn/v1"

weibo_count = 0


def gpt_35_api_stream(messages: list):
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            stream=True,
        )
        completion = {'role': '', 'content': ''}
        for event in response:
            if event['choices'][0]['finish_reason'] == 'stop':
                print("问题：", messages[0]['content'], "\n回答：", completion['content'])
                break
            for delta_k, delta_v in event['choices'][0]['delta'].items():
                completion[delta_k] += delta_v
        messages.append(completion)  # 直接在传入参数 messages 中追加消息
        return (True, completion['content'])
    except Exception as err:
        return (False, f'OpenAI API 异常: {err}')


def re_search(retext, text):
    """Regular expression search.

    Prevent exception when re.search cant find one,
    Only returns the first group.

    Args:
        retext: string, regular expression.
        text: string, text want to search.

    Returns:
        string, the matched group, None when not find.
    """
    tmp = re.search(retext, text)
    if tmp:
        return tmp.group(1)
    else:
        return None


def get_timestamp():
    """13 lengths timestamp.
    Returns:
        current timestamp.
    """
    return str(round(time() * 1000))


def get_github_trending(lock=None):
    github_url = 'https://github.com/trending'
    response = requests.get(github_url)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath("//article[@class='Box-row']")
    lock.acquire()
    github.objects.all().delete()
    for repository in sections:
        author = repository.xpath("./h2/a/span//text()")[0].strip()[:-2]
        title = repository.xpath("./h2/a/text()")[-1].strip()
        if len(repository.xpath("./p/text()")) > 0:
            description = repository.xpath("./p/text()")[0].strip()
        else:
            description = "A repository"
        href = "https://github.com" + repository.xpath("./h2/a/@href")[0]
        # print(author, title, description, href)
        # rst.append([author, title, description, href])
        github.objects.create(author=author, title=title, description=description, href=href)
    # pd.DataFrame(columns=['author', 'title', 'description', 'href'], data=rst).to_csv('githubTrending.csv')
    lock.release()


def get_zhihu_hot_topic(cookie, lock=None):
    zhihu_url = 'https://www.zhihu.com/hot'
    zhihu_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Kmyhtml, like Gecko) Chrome/113.0.5672.127  Safari/537.36',
        'cookie': cookie
    }
    response = requests.get(zhihu_url, headers=zhihu_headers)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath("//section[@class='HotItem']")
    lock.acquire()
    zhihu.objects.all().delete()
    for question in sections:
        number = question.xpath("./div[@class='HotItem-index']//text()")[0].strip()
        title = question.xpath(".//h2[@class='HotItem-title']/text()")[0].strip()
        href = question.xpath("./div[@class='HotItem-content']/a/@href")[0].strip()
        picture_path = question.xpath("./a[@class='HotItem-img']/img")
        if picture_path:
            picture_element = etree.tostring(picture_path[0], encoding='unicode')
        else:
            picture_element = '<img loading="lazy" src="https://picx.zhimg.com/80/v2-4cd83ae3d6ca76dabecf001244a62310_xl.jpg?source=4e949a73" alt="打开话题页">'
        # print(number, title, href, picture_element)
        zhihu.objects.create(number=number, title=title, href=href, picture_element=picture_element)
        # rst.append([number, title, href, picture_element])
    # pd.DataFrame(columns=['number', 'title', 'href', 'picture_element'], data=rst).to_csv('zhihuHotTopics.csv', encoding='gbk')
    lock.release()


def get_bilibili_ranking(lock=None):
    bilibili_url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    items = requests.get(bilibili_url).json()['data']['list']
    lock.acquire()
    bilibili.objects.all().delete()
    for index, item in enumerate(items):
        bilibili.objects.create(rank=index + 1, pic_href=item['pic'], title=item['title'], tname=item['tname'], link=item['short_link_v2'])
    #     rst.append([index + 1, item['pic'], item['title'], item['tname'], item['short_link_v2']])
    #     print(index + 1, item['pic'], item['title'], item['tname'], item['short_link_v2'])
    # pd.DataFrame(columns=['rank', 'pic_href', 'title', 'tname', 'link'], data=rst).to_csv('bilibiliRanking.csv')
    lock.release()


def gpt_filter(site, cue=None, mode=None, lock=None):
    if site == "zhihu":
        lock.acquire()
        current_topics = zhihu.objects.all()
        lock.release()
        if mode is not None:
            content = []
            for index in range(len(current_topics)):
                content.append([current_topics[index].number, current_topics[index].title, current_topics[index].href, current_topics[index].picture_element])
            return content
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        topics = ""
        for a in current_topics:
            topics += '（' + a.number + '） ' + a.title + '；'
        messages = [{'role': 'user',
                     'content': f'From now on, you are supposed to play the role of a proficient Chinese-speaking content auditor. You need to determine whether the given topics meet the filtering criteria based on the filtering standards and a set of numbered topic titles I provide you with. Please note that these topics are all in Chinese. You should understand the content represented by these topics and compare them with the filtering standards. Additionally, you are required to output only the topic numbers of the filtered results, separating them with commas. The following is the selection criteria in Chinese: "{cue}". And here are the numbered topics for screening: "{topics}" Please think step by step and be sure to have the right answer in the form I requested, and only output the numbers of the topics that meet the criteria in the following method in English:"the output should be: (your answers)."'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([current_topics[index - 1].number, current_topics[index - 1].title, current_topics[index - 1].href, current_topics[index - 1].picture_element])
            return content
    elif site == 'github':
        lock.acquire()
        current_topics = github.objects.all()
        lock.release()
        if mode is not None:
            content = []
            for index in range(len(current_topics)):
                content.append([current_topics[index].author, current_topics[index].title, current_topics[index].description, current_topics[index].href])
            return content
        if cue is None:
            cue = "与python相关的"
        topics = ""
        i = 1
        for a in current_topics:
            topics += '(' + str(i) + ') ' + a.title + ':' + a.description + ';'

            i = i + 1
        topics = topics.encode('gbk', errors='ignore').decode('gbk')
        messages = [{'role': 'user',
                     'content': f'From now on, you have to play the role of a senior programmer. You have knowledge of various programming languages and project-related information. You need to evaluate whether these projects meet the given selection criteria based on the numbered titles and descriptions of GitHub projects I provide you. Please guess the content of these projects and compare them with the selection criteria. Additionally, you must only output the numbers of the filtered projects, separating them with commas. Here is my selection criteria: "{cue}," and here are the numbered topics I want to filter: "{topics}." Please think step by step and be sure to have the right answer in the form I requested, and only output the numbers of the projects that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([current_topics[index - 1].author, current_topics[index - 1].title, current_topics[index - 1].description, current_topics[index - 1].href])
            return content
    elif site == 'bilibili':
        lock.acquire()
        current_topics = bilibili.objects.all()
        lock.release()
        if mode is not None:
            content = []
            for index in range(len(current_topics)):
                content.append([current_topics[index].rank, current_topics[index].title, current_topics[index].tname, current_topics[index].pic_href, current_topics[index].link])
            return content
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        topics = ""
        for a in current_topics:
            topics += '(' + str(a.rank) + ') ' + a.title + ':' + a.tname + '；'
        topics = topics.encode('gbk', errors='ignore').decode('gbk')
        messages = [{'role': 'user',
                     'content': f'From now on, you have to play the role of a proficient content auditor who is fluent in Chinese. You need to evaluate whether these videos meet the given selection criteria based on the numbered video titles and their corresponding categories. Please note that both the titles and categories are in Chinese. Please understand their content and compare them with the selection criteria. Additionally, you must only output the numbers of the filtered videos, separating them with commas. Here is my selection criteria: "{cue}," and here are the numbered video titles and categories I want to filter: "{topics}". Please think step by step and be sure to have the right answer in the form I requested, and only output the numbers of the topics that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([current_topics[index - 1].rank, current_topics[index - 1].title, current_topics[index - 1].tname, current_topics[index - 1].pic_href, current_topics[index - 1].link])
            return content
    elif site == 'weibo':
        lock.acquire()
        current_topics = weibo.objects.all()
        lock.release()
        if mode is not None:
            content = []
            for index in range(len(current_topics)):
                content.append([current_topics[index].title, current_topics[index].rank_pic_href, current_topics[index].link])
            return content
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        topics = ""
        i = 1
        for a in current_topics:
            topics += '(' + str(i) + ') ' + a.title + '；'
            i += 1
        messages = [{'role': 'user',
                     'content': f'From now on, you are supposed to play the role of a proficient Chinese-speaking content auditor. You need to determine whether the given topics meet the filtering criteria based on the filtering standards and a set of numbered topic titles I provide you with. Please note that these topics are all in Chinese. You should understand the content represented by these topics and compare them with the filtering standards. Additionally, you are required to output only the topic numbers of the filtered results, separating them with commas. The following is the selection criteria in Chinese: "{cue}". And here are the numbered topics for screening: "{topics}" Please think step by step and be sure to have the right answer in the form I requested, and only output the numbers of the topics that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([current_topics[index - 1].title, current_topics[index - 1].rank_pic_href, current_topics[index - 1].link])
            return content
    elif site == 'dekt':
        lock.acquire()
        current_topics = dektinfo.objects.all()
        lock.release()
        if mode is not None:
            content = []
            for index in range(len(current_topics)):
                content.append([index, current_topics[index].category, current_topics[index].category_url, current_topics[index].item_id, current_topics[index].activity_name, current_topics[index].active_start_time, current_topics[index].active_end_time,
                                current_topics[index].enroll_start_time, current_topics[index].enroll_end_time, current_topics[index].activity_picurl])
            content.sort(key=lambda x: x[0])
            return content
        if cue is None:
            cue = "劳动教育"
        topics = ""
        i = 1
        for a in current_topics:
            topics += '(' + str(i) + ') ' + a.category + ":" + a.activity_name + '；'
            i += 1
        messages = [{'role': 'user',
                     'content': f'From now on, you are required to play the role of a proficient Chinese-speaking content auditor. You need to evaluate whether the provided activities meet the given selection criteria based on the designated activity categories and titles, which are all in Chinese. Please understand the meaning of the categories and titles and compare them to the selection criteria. Furthermore, you should only output the numbers of the activities that pass the selection, separating them with commas. The following is the selection criteria: "{cue}". Here are the numbered video titles and categories for your evaluation: "{topics}". Please think step by step and be sure to have the right answer in the form I requested and only output the numbers of the activities that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([index, current_topics[index - 1].category, current_topics[index - 1].category_url, current_topics[index - 1].item_id, current_topics[index - 1].activity_name, current_topics[index - 1].active_start_time, current_topics[index - 1].active_end_time,
                                current_topics[index - 1].enroll_start_time, current_topics[index - 1].enroll_end_time, current_topics[index - 1].activity_picurl])
            content.sort(key=lambda x: x[0])
            return content
    elif site == 'seiee_notion':
        lock.acquire()
        current_topics = transfer_from_database_to_list("app01_seieenotification")
        lock.release()
        if mode is not None:
            return current_topics
        if cue is None:
            cue = "和学生工作相关的内容"
        topics = ""
        i = 1
        for a in current_topics:
            topics += '(' + str(i) + ') ' + a[1] + '；'
            i += 1
        messages = [{'role': 'user',
                     'content': f'From now on, you will play the role of a content auditor proficient in Chinese. You need to determine whether the provided notices meet the filtering criteria by using the filtering criteria I give you and the numbered titles of the school notices. Please note that the titles of these notices are in Chinese. Please understand their content and compare them with the filtering criteria. Additionally, you should only output the numbers of the notices that pass the filtering criteria, separating the numbers with commas. Here are my filtering criteria: "{cue}". And here are the numbered titles of the school notices to be filtered: "{topics}". Please think step by step and be sure to have the right answer in the form I requested and only output the numbers of the notices that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([index, current_topics[index - 1][1], current_topics[index - 1][2], current_topics[index - 1][3]])
            content.sort(key=lambda x: x[0])
            return content

    elif site == 'minhang_weather':
        lock.acquire()
        current_topics = minhang_24h_weather.objects.all()
        lock.release()
        content = []
        for a in current_topics:
            content.append([a.Name_of_weather_picture, a.weather_text, a.temperature, a.wind_direction, a.wind_strength, a.hour])
        return content
    elif 'shuiyuan' in site:
        lock.acquire()
        current_topics = transfer_from_database_to_list(site)
        lock.release()
        if mode is not None:
            return current_topics
        if cue is None:
            cue = "学生事务"
        topics = ""
        i = 1
        for a in current_topics:
            topics += '(' + str(i) + ') ' + a[6] + ":" + a[2] + '；'
            i += 1

        topics = topics.encode('gbk', errors='ignore').decode('gbk')
        messages = [{'role': 'user',
                     'content': f'From now on, you are going to play the role of a student. You need to determine whether the given topics meet the selection criteria I provide you with, along with a list of numbered topic categories and topic names. Please note that the topics are in Chinese. It is important to understand their content and compare them to the selection criteria. Additionally, you should only output the numbers of the topics that pass the filtering criteria, separating the numbers with commas. Here are my filtering criteria: "{cue}". And here are the numbered topic categories and topic names to be filtered: "{topics}". Please think step by step and be sure to have the right answer in the form I requested and only output the numbers of the topics that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([index, current_topics[index - 1][1], current_topics[index - 1][2], current_topics[index - 1][3], current_topics[index - 1][4], current_topics[index - 1][5], current_topics[index - 1][6], current_topics[index - 1][7]])
            content.sort(key=lambda x: x[0])
            return content
    elif 'calendar' in site:
        lock.acquire()
        current_topics = transfer_from_database_to_list(site)
        lock.release()
        current_topics.sort(key=lambda x: x[0])  # 根据第一个字符串进行排序
        return current_topics
    elif 'canvas' in site:
        lock.acquire()
        current_topics = transfer_from_database_to_list(site)
        lock.release()
        if mode is not None:
            return current_topics
        if cue is None:
            cue = "作业"
        topics = ""
        i = 1
        for a in current_topics:
            topics += '(' + str(i) + ') ' + a[4] + ":" + a[6] + '；'
            i += 1
        messages = [{'role': 'user',
                     'content': f'From now on, you are going to play the role of a student. You need to determine whether the given assignments meet the selection criteria I provide you with, along with a list of numbered courses and assignments. Please note that the titles of these assignments are in Chinese. It is important to understand their content and compare them to the selection criteria Additionally, you should only output the numbers of the assignments that pass the filtering criteria, separating the numbers with commas. Here are my filtering criteria: "{cue}". And here are the numbered courses and assignments to be filtered: "{topics}". Please think step by step and be sure to have the right answer in the form I requested and only output the numbers of the assignments that meet the criteria in the following method in English:"the output should be: (your answers).".'}]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return []
        else:
            content = []
            if re.search(r'the output should be:(.*)', ans[1]) is None:
                numbers = re.findall(r'Based on*?\((\d+)\)', ans[1])
                # 转换为整数数组
                numbers = [int(match) for match in numbers]
            else:
                numbers = sorted([int(item) for item in
                                  (set(re.findall(r'\d+', re.search(r'the output should be:(.*)', ans[1]).group(1))))])
            for index in numbers:
                content.append([index, current_topics[index - 1][1], current_topics[index - 1][2], current_topics[index - 1][3], current_topics[index - 1][4], current_topics[index - 1][5], current_topics[index - 1][6], current_topics[index - 1][7]])
            content.sort(key=lambda x: x[0])
            return content


def get_weibo_hot_topic(lock=None):
    global weibo_count
    weibo_url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
    items = requests.get(weibo_url).json()['data']['cards'][0]['card_group']
    weibo_session = requests.Session()
    weibo_items = []
    current_turn_folder_path = "SJTUhelperv5/app01/static/img/weibo/" + str(weibo_count) + "/"
    shutil.rmtree(current_turn_folder_path)
    os.mkdir(current_turn_folder_path)
    for index, item in enumerate(items):
        resp_from_weibo = weibo_session.get("https://m.weibo.cn/api/container/getIndex?" + item['scheme'][26:] + "&page_type=searchall")
        try:
            resp = weibo_session.get(resp_from_weibo.json()['data']["cardlistInfo"]["cardlist_head_cards"][0]['head_data']["portrait_url"])
        except Exception as e:
            resp = weibo_session.get(item["pic"])
        pic_path = current_turn_folder_path + str(index) + ".jpg"
        with open(pic_path, 'wb') as f:
            f.write(resp.content)
        pic_path = pic_path[26:]
        weibo_items.append([pic_path, item['desc'], item['scheme']])
    lock.acquire()
    weibo.objects.all().delete()
    for item in weibo_items:
        weibo.objects.create(rank_pic_href=item[0], title=item[1], link=item[2])
    lock.release()
    weibo_count = (weibo_count + 1) % 3

    # lock.acquire()
    # weibo.objects.all().delete()
    # for index, item in enumerate(items):
    #     weibo.objects.create(rank_pic_href=item['pic'], title=item['desc'], link=item['scheme'])
    #     rst.append([item['pic'], item['desc'], item['scheme']])
    #     print([item['pic'], item['desc'], item['scheme']])
    # pd.DataFrame(columns=['rank_pic_href', 'title', 'link'], data=rst).to_csv('weiboRanking.csv')
    # lock.release()


def get_minhang_24h_weather(lock=None):
    minhang_weather_url = "https://www.tianqi.com/minhang/"
    myheaders = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127  Safari/537.36'}
    response = requests.get(minhang_weather_url, headers=myheaders)
    myhtml = etree.HTML(response.text)

    weather_pic_headers = {
        "authority": "static.tianqistatic.com",
        "method": "GET",
        "path": "/static/tianqi2018/ico2/b1.png",
        "scheme": "https",
        "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "If-Modified-Since": "Mon, 30 Mar 2020 16:17:18 GMT",
        "If-None-Match": '"5e821b8e-13c8"',
        "Referer": "https://www.tianqi.com/",
        "Sec-Ch-Ua": '"Microsoft Edge";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.43"
    }
    weather_pics_path = 'SJTUhelperv5/weather_pics'  # 由views.py调用
    existing_weather_pics = os.listdir(weather_pics_path)
    rst = [[], [], [], [], [], []]  # 依次为该小时的 已保存到本地的天气图片的名称，天气文字，气温，风向，风力，小时
    sections = myhtml.xpath("//div[@class='twty_hour']/div/div")
    for item in sections:
        for pic in item.xpath("./ul[1]/li"):
            pic_url = pic.xpath("./img/@src")[0]
            pic_name = re.search(r'\/([^\/]*)$', pic_url).group(1)
            if pic_name not in existing_weather_pics:
                response = requests.get("https:" + pic_url, headers=weather_pic_headers)
                if response.status_code == 200:
                    with open(weather_pics_path + '/' + pic_name, 'wb') as file:
                        file.write(response.content)
                        print('图片保存成功')
                else:
                    print('请求失败:', response.status_code)
                existing_weather_pics = os.listdir(weather_pics_path)
            rst[0].append(pic_name)
        for weather in item.xpath("./ul[2]/li"):
            rst[1].append(weather.xpath("./text()")[0])
        for temperature in item.xpath("./div/ul/li"):
            rst[2].append(temperature.xpath("./span/text()")[0])
        for wind_direction in item.xpath("./ul[3]/li"):
            rst[3].append(wind_direction.xpath("./text()")[0])
        for wind_strength in item.xpath("./ul[4]/li"):
            rst[4].append(wind_strength.xpath("./text()")[0])
        for hour in item.xpath("./ul[5]/li"):
            rst[5].append(hour.xpath("./text()")[0])
    lock.acquire()
    minhang_24h_weather.objects.all().delete()
    for i in range(len(rst[0])):
        minhang_24h_weather.objects.create(Name_of_weather_picture=rst[0][i], weather_text=rst[1][i], temperature=rst[2][i], wind_direction=rst[3][i], wind_strength=rst[4][i], hour=rst[5][i])
    lock.release()


'''*************SJTU板块*************'''


def autocaptcha(path):
    im = Image.open(path)
    im = im.convert('L')
    im = ImageEnhance.Contrast(im)
    im = im.enhance(3)
    img2 = Image.new('RGB', (150, 60), (255, 255, 255))
    img2.paste(im.copy(), (25, 10))
    return pytesseract.image_to_string(img2)


def _debug_show_resp(resp, addition_msg=None):
    print("----------------------------------------------------")
    if addition_msg is not None:
        print("*****", addition_msg, "*****")
    print("request:", resp.request.url)
    print("req headers:", resp.request.headers)
    print("response:", resp.url)
    print(resp.headers)
    print(resp.cookies)
    print(resp.status_code)
    if resp.status_code == 302:
        print("Redirecting->", resp.headers['Location'])
    print("----------------------------------------------------")


def auto_jaccount_authorize(location, username, password):
    oauth_session = requests.Session()
    myheaders_for_oauth = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    while True:
        try:
            resp_from_oauth = oauth_session.get(location, headers=myheaders_for_oauth)
            oauth_session, data = process_captcha_and_GA(resp_from_oauth, oauth_session, username, password)
            resp_from_ulogin = oauth_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', headers=myheaders_for_oauth, data=data, allow_redirects=False)
            err_type = re.search(r'err=(.*)$', resp_from_ulogin.headers['Location'])
            if err_type is None:
                pass
            elif err_type.group(1) == '0':
                print("Wrong username or password! Recheck!", "https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'])
                return "Wrong username or password! Recheck!", 1
            elif err_type.group(1) == '1':
                print("Wrong Captcha, retrying!", "https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'], "\r", end='')
                continue
            elif err_type.group(1) == '16':
                print("Wrong too many times, please wait a moment")
                return "Wrong too many times, please wait a moment", 0
            else:
                print("Other error", resp_from_ulogin.headers['Location'])
                continue
            resp_from_jalogin = oauth_session.get("https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            resp_from_oauth2_authorize = oauth_session.get(resp_from_jalogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            break
        except Exception as e:
            print("oops!retrying...", str(e))
            continue
    return oauth_session.cookies, resp_from_oauth2_authorize.headers['Location']


def process_captcha_and_GA(resp, session, username, password):
    captcha_id = re_search(r'img.src = \'captcha\?(.*)\'', resp.text)
    if not captcha_id:
        print('Captcha not found! Retrying...')
        return -999
    captcha_id += get_timestamp()
    captcha_url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?' + captcha_id
    captcha = requests.get(captcha_url, cookies=session.cookies, headers={'Referer': 'https://jaccount.sjtu.edu.cn/jaccount', 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"})
    with open('captcha.jpeg', 'wb') as f:
        f.write(captcha.content)
    code = autocaptcha('captcha.jpeg').strip()
    sid = re_search(r'sid" value="(.*?)"', resp.text)
    returl = re_search(r'returl" value="(.*?)"', resp.text)
    se = re_search(r'se" value="(.*?)"', resp.text)
    client = re_search(r'client" value="(.*?)"', resp.text)
    uuid = re_search(r'captcha\?uuid=(.*?)&t=', resp.text)
    if not (sid and returl and se and uuid):
        print('Params not found! Retrying...')
        return -888
    data = {'sid': sid, 'returl': returl, 'se': se, 'client': client, 'user': username,
            'pass': password, 'captcha': code, 'v': "", 'uuid': uuid}
    GA_cookie = _get_GA()
    session.cookies.update(GA_cookie)

    return session, data


def load_cookies(username):
    cookiejar = http.cookiejar.CookieJar()
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables  WHERE table_name = '{}');".format(username))
    if cursor.fetchone()[0] == 0:
        return None
    sql = "SELECT * FROM `{}`".format(username)
    # 4.执行sql语句
    cursor.execute(sql)
    i = 1
    while True:
        row = cursor.fetchone()
        if not row:
            break
        cookie = http.cookiejar.Cookie(
            version=0,
            name=row[1],
            value=row[2],
            port=None,
            port_specified=False,
            domain=row[3],
            domain_specified=True,
            domain_initial_dot=False,
            path=row[4],
            path_specified=True,
            secure=bool(row[5]),
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest=None,
            rfc2109=False
        )
        cookiejar.set_cookie(cookie)

    return cookiejar


def save_cookies(username, cookies):
    delete_dynamic_model('cookies_' + username)
    create_dynamic_model_cookies(username)
    for cookie in cookies:
        insert_dynamic_model_cookies(table_name=username, name=cookie.name, value=cookie.value, domain=cookie.domain, path=cookie.path, secure=cookie.secure)


def _get_GA():
    GA_cookie = http.cookiejar.CookieJar()
    GA_cookie.set_cookie(http.cookiejar.Cookie(version=0, name='_ga',
                                               value='GA1.3.' + str(random.randrange(100000000, 1000000000)) + '.' + str(int(time())),
                                               port=None,
                                               port_specified=False,
                                               domain='.sjtu.edu.cn',
                                               domain_specified=True,
                                               domain_initial_dot=False,
                                               path='/',
                                               path_specified=True,
                                               secure=False,
                                               expires=None,
                                               discard=True,
                                               comment=None,
                                               comment_url=None,
                                               rest={'HttpOnly': None},
                                               rfc2109=False
                                               ))
    GA_cookie.set_cookie(http.cookiejar.Cookie(version=0, name='_gid',
                                               value='GA1.3.' + str(random.randrange(100000000, 1000000000)) + '.' + str(int(time())),
                                               port=None,
                                               port_specified=False,
                                               domain='.sjtu.edu.cn',
                                               domain_specified=True,
                                               domain_initial_dot=False,
                                               path='/',
                                               path_specified=True,
                                               secure=False,
                                               expires=None,
                                               discard=True,
                                               comment=None,
                                               comment_url=None,
                                               rest={'HttpOnly': None},
                                               rfc2109=False
                                               ))
    GA_cookie.set_cookie(http.cookiejar.Cookie(version=0, name='_gat',
                                               value='1',
                                               port=None,
                                               port_specified=False,
                                               domain='.sjtu.edu.cn',
                                               domain_specified=True,
                                               domain_initial_dot=False,
                                               path='/',
                                               path_specified=True,
                                               secure=False,
                                               expires=None,
                                               discard=True,
                                               comment=None,
                                               comment_url=None,
                                               rest={'HttpOnly': None},
                                               rfc2109=False
                                               ))
    GA_cookie.set_cookie(http.cookiejar.Cookie(version=0, name='_ga_QP6YR9D8CK',
                                               value='GS1.3.' + str(int(time())) + '.1.0.' + str(int(time())) + '.0.0.0',
                                               port=None,
                                               port_specified=False,
                                               domain='.sjtu.edu.cn',
                                               domain_specified=True,
                                               domain_initial_dot=False,
                                               path='/',
                                               path_specified=True,
                                               secure=False,
                                               expires=None,
                                               discard=True,
                                               comment=None,
                                               comment_url=None,
                                               rest={'HttpOnly': None},
                                               rfc2109=False
                                               ))
    return GA_cookie


def dekt_save_data(resp_from_section, category, category_url):
    current_time = time() * 1000
    for item in resp_from_section.json()['rows']:
        status_enroll = "【报名中】"
        status_activity = "活动未开始"
        if item['enrollStartTime'] is not None:
            if item['enrollStartTime'] > current_time:
                status_enroll = "报名未开始"
            enrollStartTime = strftime('%Y年%m月%d日 %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = strftime('%Y年%m月%d日 %H:%M:%S', localtime(0))
        if item['enrollEndTime'] < current_time:
            status_enroll = "报名已结束"
        if item['activeStartTime'] < current_time:
            status_activity = "活动进行中"
        if item['activeEndTime'] < current_time:
            status_activity = "活动已结束"
        dektinfo.objects.create(category=category, category_url=category_url, item_id=status_enroll + "|" + status_activity, activity_name=item['activityName'], enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y年%m月%d日 %H:%M:%S', localtime(item['enrollEndTime'] / 1000)), active_start_time=strftime('%Y年%m月%d日 %H:%M:%S', localtime(item['activeStartTime'] / 1000)),
                                active_end_time=strftime('%Y年%m月%d日 %H:%M:%S', localtime(item['activeEndTime'] / 1000)), activity_picurl=item['activityPicurl'])


def process_dekt(username=None, password=None, lock=None, lock1=None):
    user_cookie = None
    if password is None:
        lock.acquire()
        user_cookie = load_cookies('cookies_' + username)
        lock.release()
    myheaders_for_dekt = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "dekt.sjtu.edu.cn"}
    dekt_login_url = 'https://jaccount.sjtu.edu.cn/oauth2/authorize?response_type=code&client_id=sowyD3hGhP6f6O92bevg&redirect_uri=https://dekt.sjtu.edu.cn/h5/index&state=&scope=basic'

    if user_cookie is None:
        print("now trying to log into [dekt]")
        if username is None or password is None:
            raise ValueError("未输入用户名和密码！")
        user_cookie, jump_url = auto_jaccount_authorize(dekt_login_url, username, password)
        lock.acquire()
        save_cookies(username, user_cookie)
        lock.release()
        dekt_session = requests.Session()
        dekt_session.cookies.update(user_cookie)
    else:
        print("already logged in, entering [dekt]")
        oauth_session = requests.Session()
        dekt_session = requests.Session()
        oauth_session.cookies.update(user_cookie)
        dekt_session.cookies.update(user_cookie)
        jump_url = oauth_session.get(dekt_login_url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}).request.url

    myheaders_for_dekt['Content-Type'] = "application/json"
    resp_from_dekt = dekt_session.post("https://dekt.sjtu.edu.cn/api/auth/secondclass/loginByJa?time=" + str(round(time() * 1000)) + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"code": jump_url[39:], "redirect_uri": "https://dekt.sjtu.edu.cn/h5/index", "scope": "basic", "client_id": "sowyD3hGhP6f6O92bevg", "publicaccountid": "sjtuvirtual"}))
    if resp_from_dekt.json()['code'] == 1:
        lock.acquire()
        delete_dynamic_model('cookies_' + username)
        lock.release()
        print("Cookies expired! Please login again!")
        raise ValueError("重定向到登录页面！")
        return
    token = resp_from_dekt.json()['data']['token']
    myheaders_for_dekt.update({'Jtoken': resp_from_dekt.json()['data']['jtoken'], 'Curuserid': "null"})

    resp_from_hszl = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 0, "redTour": 1}, "publicaccountid": "sjtuvirtual"}))
    lock1.acquire()
    dektinfo.objects.all().delete()
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "hszl done")
    dekt_save_data(resp_from_hszl, "红色之旅", "https://dekt.sjtu.edu.cn/h5/activities?categoryName=%E7%BA%A2%E8%89%B2%E4%B9%8B%E6%97%85&redTour=1")
    resp_from_ldjy = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 1, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "ldjy done")
    dekt_save_data(resp_from_ldjy, "劳动教育", "https://dekt.sjtu.edu.cn/h5/activities?categoryName=%E5%8A%B3%E5%8A%A8%E6%95%99%E8%82%B2&laborEducation=1")
    resp_from_zygy = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "zygy", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "zygy done")
    dekt_save_data(resp_from_zygy, "志愿公益", "https://dekt.sjtu.edu.cn/h5/activities?categoryCode=zygy&categoryName=%E5%BF%97%E6%84%BF%E5%85%AC%E7%9B%8A")
    resp_from_wthd = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "yshd", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "wthd done")
    dekt_save_data(resp_from_wthd, "文体活动", "https://dekt.sjtu.edu.cn/h5/activities?categoryCode=yshd&categoryName=%E6%96%87%E4%BD%93%E6%B4%BB%E5%8A%A8")
    resp_from_kjcx = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "kjcx", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "kjcx done")
    dekt_save_data(resp_from_kjcx, "科技创新", "https://dekt.sjtu.edu.cn/h5/activities?categoryCode=kjcx&categoryName=%E7%A7%91%E6%8A%80%E5%88%9B%E6%96%B0")
    resp_from_jtjz = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "jtjz", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    print(strftime("%Y-%m-%d %H:%M:%S", localtime()), "jtjz done")
    dekt_save_data(resp_from_jtjz, "讲坛讲座", "https://dekt.sjtu.edu.cn/h5/activities?categoryCode=jtjz&categoryName=%E8%AE%B2%E5%9D%9B%E8%AE%B2%E5%BA%A7")
    # resp_from_qt = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
    #                                  data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "qt", "topicCode": "", "statusType": "", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    # dekt_save_data(resp_from_qt,"其他","https://dekt.sjtu.edu.cn/h5/activities?categoryCode=qt&categoryName=%E5%85%B6%E4%BB%96")
    lock1.release()
    print("dekt success!!!")
    return 1


def process_canvas(username=None, password=None, lock=None, lock1=None):
    user_cookie = None
    if password is None:
        lock.acquire()
        user_cookie = load_cookies('cookies_' + username)
        lock.release()
    try:
        df = pd.read_csv('course_id_name_dict.csv')
        course_id_name_dict = df.set_index(df.columns[0]).to_dict()[df.columns[1]]
    except FileNotFoundError:
        course_id_name_dict = {}
    canvas_login_url = 'https://oc.sjtu.edu.cn/login/canvas'
    myheaders_for_oc = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "oc.sjtu.edu.cn"}
    oc_session = requests.Session()
    if user_cookie is None:
        print("now trying to log into [canvas]")
        if username is None or password is None:
            return False
            raise ValueError("未输入用户名和密码！")
        oc_session.get(canvas_login_url, headers=myheaders_for_oc)
        resp_from_openid_connect = oc_session.get("https://oc.sjtu.edu.cn/login/openid_connect", headers=myheaders_for_oc, allow_redirects=False)
        user_cookie, jump_url = auto_jaccount_authorize(resp_from_openid_connect.headers['Location'], username, password)
        lock.acquire()
        save_cookies(username, user_cookie)
        lock.release()
        oc_session.cookies.update(user_cookie)

    else:
        print("already logged in, entering [canvas]")
        oc_session.cookies.update(user_cookie)
        resp = oc_session.get(canvas_login_url, headers=myheaders_for_oc)
        resp = oc_session.get("https://oc.sjtu.edu.cn/login/openid_connect", headers=myheaders_for_oc, allow_redirects=False)
        oauth_session = requests.Session()
        oauth_session.cookies.update(user_cookie)
        initial_url = resp.headers['Location']
        while True:
            response = oauth_session.get(initial_url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}, allow_redirects=False)
            if response.status_code == 302:
                jump_url = response.headers['Location']
                if 'https://oc.sjtu.edu.cn/login' in jump_url:
                    break
                initial_url = jump_url
            else:
                break

    resp_from_oc = oc_session.get(jump_url, headers=myheaders_for_oc)
    planner_data = oc_session.get("https://oc.sjtu.edu.cn/api/v1/planner/items?start_date=" + strftime("%Y-%m-%d", localtime(time() + (-7 * 24 * 60 * 60))) + "&order=asc&per_page=100", headers=myheaders_for_oc)
    if planner_data.status_code != 200:
        print("Cookies expired! Please login again!")
        raise ValueError("重定向到登录页面！")
    json_data = json.loads(planner_data.text[9:])
    lock1.acquire()
    delete_dynamic_model_canvas(username)
    create_dynamic_model_canvas(username)
    for item in json_data:
        if item['course_id'] not in course_id_name_dict:
            get_course_name_resp = oc_session.get("https://oc.sjtu.edu.cn/courses/" + str(item['course_id']), headers=myheaders_for_oc)
            course_id_name_dict[item['course_id']] = etree.HTML(get_course_name_resp.text).xpath("//title//text()")[0]
        if 'due_at' not in item['plannable']:
            due_at = '/'
        else:
            due_at = strftime("%Y-%m-%d+%H:%M:%S", localtime(mktime(strptime(item['plannable']['due_at'], "%Y-%m-%dT%H:%M:%SZ")) + 8 * 60 * 60))
        if item['submissions'] == "false" or item['submissions'] == False:
            submit = "Not required"
        else:
            if item['submissions']['submitted'] == False or item['submissions']['submitted'] == "false":
                if item['planner_override'] is not None:
                    submit = "true"
                else:
                    submit = 'false'
            else:
                submit = "true"
        if 'description' not in item['plannable']:
            descript = "/"
        else:
            descript = item['plannable']['description']
        if 'name' in item['plannable']:
            name = item['plannable']['name']
        else:
            name = item['plannable']['title']
        insert_dynamic_model_canvas(table_name=username, due_at=due_at, submit=submit, plannable_id=item['plannable_id'], course_id_name_dict=course_id_name_dict[item['course_id']], descript=descript, _name=name, html_url=item['plannable']['html_url'])
    lock1.release()
    print("canvas success!!!")


shuiyuan_category_dict = {'60': '校友之家', '53': '水源站务', '61': '课业学习', '68': '音乐之声', '54': '站务公告', '70': '二〇新声', '46': '宠物花草', '51': '极客时间', '41': 'g_jwc', '49': 'g_library', '50': '青年之声', '66': '硬件产品', '55': 'g_nic', '64': '滋滋猪鸡', '71': 'g_piano', '62': '溯·源', '69': '心情驿站', '45': '热点新闻', '2': '我的帖子',
                          '10': '社会信息', '11': 'trust_level_1', '12': 'trust_level_2', '13': '社团组织', '14': 'trust_level_4', '3': 'Review', '1': 'Topics', '31': '讲座报告', '43': 'Isabelle', '28': 'Graceful', '29': '二手交易', '36': '学在交大', '85': '科研科创', '37': '本科生教务', '38': '研究生教务', '96': '院系天地',
                          '23': '校园生活', '20': '交大动态', '32': '校园服务', '101': '校园网络', '106': '正版软件', '33': '失物招领', '87': '人生经验', '78': '医疗健康', '89': '学习进阶', '90': '逢考必过', '91': '境外求索', '92': '职场生涯', '35': '水源广场', '84': '聊聊水源', '63': '谈笑风生', '75': '深度讨论', '58': '相约鹊桥', '52': '知性感性', '107': '出行贴士',
                          '79': '文化艺术', '30': '演出活动', '47': '影视品论', '59': '文学交流', '83': '摄影天地', '80': '泛二次元', '22': '休闲娱乐', '67': '游戏竞技', '81': '游山玩水', '82': '美妆时尚', '94': '运动健身', '95': '体育赛事', '76': '数码科技', '77': '软件应用', '26': '租房信息', '93': '招生信息', '24': '招聘信息', '72': '广而告之', '97': '赏金客栈',
                          '98': '爱心屋', '99': '晨曦社', '102': 'Minecraft 社', '100': 'SJTU-Plus', '109': '浮泽动漫协会', '111': '钢琴协会', '74': '水源教程', '65': '水源活动', '104': '水源档案馆', '105': '封校时光', '110': '封校时光 2.0', '56': 'Zoom背景', '108': '过时内容', '4': 'Admin', '5': 'Users', '6': 'About', '7': 'FAQ',
                          '8': 'Groups', '9': 'Badges'}


def update_shuiyuan_category(shuiyuan_session, default_headers):
    response = shuiyuan_session.get("https://shuiyuan.sjtu.edu.cn/categories", headers=default_headers)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath('//div[@class="hidden" and @id="data-preloaded"]')[0]
    data_preloaded = sections.get('data-preloaded')
    matches = re.findall(r'id\\":(\d*),\\"name\\":\\"(.*?\\)', data_preloaded)
    shuiyuan_category_dict = {}
    for match in matches:
        shuiyuan_category_dict[match[0]] = match[1][:-1]
    print(shuiyuan_category_dict)


def process_shuiyuan(username=None, password=None, lock=None, lock1=None):
    user_cookie = None
    if password is None:
        lock.acquire()
        user_cookie = load_cookies('cookies_' + username)
        lock.release()
    shuiyuan_login_url = "https://shuiyuan.sjtu.edu.cn/session/csrf"
    shuiyuan_session = requests.Session()
    default_headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "shuiyuan.sjtu.edu.cn"}
    myheaders_for_shuiyuan = {
        "Sec-Ch-Ua": '"Chromium";v="113", "Not-A.Brand";v="24"',
        "Discourse-Present": "true",
        "X-Csrf-Token": "undefined",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36",
        "Accept": "application/json, text/javascript, */*;q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://shuiyuan.sjtu.edu.cn/login",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    shuiyuan_resp1 = shuiyuan_session.get(shuiyuan_login_url, headers=myheaders_for_shuiyuan)
    data = {'authenticity_token': shuiyuan_resp1.text[9:-2]}
    resp_from_auth_jaccount = shuiyuan_session.post("https://shuiyuan.sjtu.edu.cn/auth/jaccount", headers=default_headers, data=data, allow_redirects=False)

    if user_cookie is None:
        print("now trying to log into [shuiyuan]")
        if username is None or password is None:
            raise ValueError("未输入用户名和密码！")
        user_cookie, jump_url = auto_jaccount_authorize(resp_from_auth_jaccount.headers['Location'], username, password)
        lock.acquire()
        save_cookies(username, user_cookie)
        lock.release()
    else:
        print("already logged in, entering [shuiyuan]")
        oauth_session = requests.Session()
        oauth_session.cookies.update(user_cookie)
        jump_url = oauth_session.get("https://shuiyuan.sjtu.edu.cn/auth/jaccount", headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}).request.url

    shuiyuan_session.cookies.update(user_cookie)
    resp_from_shuiyuan = shuiyuan_session.get(jump_url, headers=myheaders_for_shuiyuan)
    resp_from_latest = shuiyuan_session.get("https://shuiyuan.sjtu.edu.cn/latest.json?ascending=false", headers=default_headers)
    if resp_from_latest.status_code != 200:
        delete_dynamic_model('cookies_' + username)
        print("Cookies expired! Please login again!")
        raise ValueError("重定向到登录页面！")
        return
    infos = resp_from_latest.json()['topic_list']['topics']
    lock1.acquire()
    delete_dynamic_model_shuiyuan(username)
    create_dynamic_model_shuiyuan(username)
    for index, item in enumerate(infos):
        ref = "https://shuiyuan.sjtu.edu.cn/t/topic/" + str(item['id'])
        if 'last_read_post_number' in item:
            ref += '/' + str(item['last_read_post_number'])
        if item['tags'] != []:
            tags = ""
            for data in item['tags']:
                tags += data
            item['tags'] = tags
        insert_dynamic_model_shuiyuan(table_name=username, ref=ref, title=item['title'], posts_count=item['posts_count'], reply_count=item['reply_count'], unseen=item['unseen'], shuiyuan_category_dict=shuiyuan_category_dict[str(item['category_id'])], tags=item['tags'], views=item['views'])
    # 仅当category字典需要更新时才调用此函数
    # update_shuiyuan_category(shuiyuan_session,default_headers)
    lock1.release()
    print("shuiyuan success!!!")
    return 1


def mysjtu_calendar(username=None, password=None, beginfrom=-730, endat=365, lock=None, lock1=None):  # beginfrom和endat均是相对今天而言
    user_cookie = None
    lock1.acquire()
    if password is None:
        lock.acquire()
        user_cookie = load_cookies('cookies_' + username)
        lock.release()
    mysjtu_url = "https://my.sjtu.edu.cn/ui/calendar/"
    default_headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36",
        'Host': "my.sjtu.edu.cn"}
    myheaders_for_oauth = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36",
        'Host': "jaccount.sjtu.edu.cn"}
    oauth_session = requests.Session()
    if user_cookie is None:
        print("now trying to log into [mysjtu]")
        if username is None or password is None:
            raise ValueError("未输入用户名和密码！")
        mysjtu_session = requests.Session()
        resp_from_mysjtu = mysjtu_session.get(mysjtu_url, headers=default_headers, allow_redirects=False)
        resp_from_mysjtu = mysjtu_session.get("https://my.sjtu.edu.cn" + resp_from_mysjtu.headers['Location'],
                                              headers=default_headers, allow_redirects=False)
        while True:
            try:
                resp_from_oauth = oauth_session.get(resp_from_mysjtu.headers['Location'],
                                                    headers=myheaders_for_oauth)
                oauth_session, data = process_captcha_and_GA(resp_from_oauth, oauth_session, username, password)
                resp_from_ulogin = oauth_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin',
                                                      headers=myheaders_for_oauth, data=data, allow_redirects=False)
                resp_from_jalogin = oauth_session.get(
                    "https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'],
                    headers=myheaders_for_oauth, allow_redirects=False)
                resp_from_oauth2_authorize = oauth_session.get(resp_from_jalogin.headers['Location'],
                                                               headers=myheaders_for_oauth, allow_redirects=False)
                break
            except Exception:
                print("oops!retrying...")
                continue
        user_cookie = oauth_session.cookies
        lock.acquire()
        save_cookies(username, user_cookie)
        lock.release()
        mysjtu_session.cookies.update(oauth_session.cookies)
        mysjtu_session.get(resp_from_oauth2_authorize.headers['Location'], headers=default_headers)
    else:
        print("already logged in, entering [mysjtu]")
        oauth_session.cookies.update(user_cookie)
        if username is None:
            username = "数据库内用户名"

    calendar_session = requests.Session()
    calendar_session.cookies.update(user_cookie)
    calendar_headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36",
        'Host': "calendar.sjtu.edu.cn"}
    aa = calendar_session.get("https://calendar.sjtu.edu.cn/?tenantUserId=" + username, headers=calendar_headers,
                              allow_redirects=False)
    aa = calendar_session.get(aa.headers['Location'], headers=calendar_headers, allow_redirects=False)
    initial_url = aa.headers['Location']
    # 自动跳转，当跳转到calendar.sjtu.edu.cn/login下时终止并切换会话
    while True:
        response = oauth_session.get(initial_url, headers=myheaders_for_oauth, allow_redirects=False)
        if response.status_code == 302:
            redirect_url = response.headers['Location']
            if 'https://calendar.sjtu.edu.cn/login' in redirect_url:
                break
            initial_url = redirect_url
        else:
            break
    calendar_session.get(redirect_url, headers=calendar_headers)
    get_tables_id = calendar_session.get("https://calendar.sjtu.edu.cn/api/calendar/list", headers=calendar_headers).json()['data']['my']
    tables = []
    for table in get_tables_id:
        tables.append([table['name'], table['id']])
    delete_dynamic_model_tablesid(username)
    create_dynamic_model_tablesid(username)
    for table in tables:
        insert_dynamic_model_tablesid(table_name=username, name=table[0], value=table[1])

    next_week_calendar_url = "https://calendar.sjtu.edu.cn/api/event/list?startDate=" + strftime("%Y-%m-%d",
                                                                                                 localtime(
                                                                                                     time() + (
                                                                                                             beginfrom * 24 * 60 * 60))) + "+00:00&endDate=" + strftime(
        "%Y-%m-%d", localtime(time() + (endat * 24 * 60 * 60))) + "+00:00&weekly=false&ids="
    calendar_list = calendar_session.get(next_week_calendar_url, headers=calendar_headers, allow_redirects=False)
    if calendar_list.status_code != 200:
        delete_dynamic_model('cookies_' + username)
        print("Cookies expired! Please login again!")
        raise ValueError("重定向到登录页面！")
    delete_dynamic_model_calendar(username)
    tmp_lock=threading.Lock()
    tmp_lock.acquire()
    create_dynamic_model_calendar(username)
    tmp_lock.release()
    for event in calendar_list.json()['data']['events']:
        insert_dynamic_model_calendar(table_name=username, title=event["title"], starttime=event["startTime"],
                                      endtime=event["endTime"], location=event["location"],
                                      json_detail_url=event['eventId'], allday=event['allDay'])

    # return calendar_session.cookies
    create_dynamic_model_cookies(username + 'store')
    delete_dynamic_model('cookies_' + username + 'store')
    create_dynamic_model_cookies(username + 'store')
    for cookie in calendar_session.cookies:
        insert_dynamic_model_cookies(table_name=username + 'store', name=cookie.name, value=cookie.value, domain=cookie.domain, path=cookie.path, secure=cookie.secure)
    lock1.release()
    print("calendar success!!!")
    return


"""************************* 数据格式说明 *******************************
变量名                 含义                       类型          格式
title               日程名                      字符串         不可为空
startTime           日程开始时间                 字符串         形如2023-10-1 23:00 
endTime             日程结束时间                 字符串         形如2023-10-1 23:00 
status              日程状态                    字符串         在忙 or 空闲 or 不在办公室 三者中的一个
reminderMinutes     日程开始前多少分钟进行提醒      整数          日程不提醒时设为缺省值-1，否则为非负整数，建议为0,5,10，30，60，1440,10080中的值
allDay              是否为全天事件               布尔值         默认为False
location            日程地点                    字符串         可为空
description         日程描述                    字符串         可为空
schedule_type       日程种类                    字符串         课程 or 会议 or 私人 三者中的一个
recurrence          日程重复状态                 None 或 字典   字典形如 {"endDate":"2024-9-30 23:59","rangeType":"EndDate","patternType":"Weekly","intervalNumber":1}
                                                                endDate         字符串         形如2024-9-30 23:59
                                                                rangeType       固定为字符串EndDate
                                                                patternType     与intervalNumber搭配使用，可选组合如下：(Daily,1),(Weekly,1),(Weekly,2),(AbsoluteMonthly,1),(AbsoluteYearly,1)
"""


# required_cookies应包括 _ga 与 _ga_QP6YR9D8CK 与 JSESSIONID
def create_schedule(required_cookies, title, startTime, endTime, status, reminderMinutes=-1, allDay=False, location="", description="", schedule_type="私人", recurrence=None):
    schedule_data = {"allDay": allDay, "body": description, "endTime": endTime, "importance": "LOW", "location": location, "reminderMinutes": reminderMinutes, "recurrence": recurrence, "status": status, "recurrenceEndDate": "", "startTime": startTime, "title": title, "extremity": False,
                     'calendarId': schedule_type}
    if reminderMinutes == -1:
        schedule_data['reminderOn'] = False
    else:
        schedule_data['reminderOn'] = True
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "calendar.sjtu.edu.cn", 'Content-Type': "application/json;charset=UTF-8"}
    resp = requests.post("https://calendar.sjtu.edu.cn/api/event/create", headers=myheaders, data=json.dumps(schedule_data), cookies=required_cookies, allow_redirects=False).json()
    if not resp['success']:
        print("Creation failure due to", resp['msg'])
        return 0
    else:
        print("Create schedule success!")


# required_cookies应包括 JSESSIONID
# 要删除的任务不存在时也会返回删除成功
def delete_schedule(required_cookies, task_id):
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "calendar.sjtu.edu.cn"}
    resp = requests.post("https://calendar.sjtu.edu.cn/api/event/delete", headers=myheaders, data={'id': task_id, 'type': 1}, cookies=required_cookies).json()
    if resp['success']:
        print("delete success!")
    else:
        print(resp['msg'])


def seiee_notification(getpages=1, lock=None):
    seiee_url = 'https://www.seiee.sjtu.edu.cn/xsgz_tzgg_xssw.html'
    lock.acquire()
    seieeNotification.objects.all().delete()
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "www.seiee.sjtu.edu.cn"}
    seiee_session = requests.Session()
    seiee_session.get(seiee_url, headers=myheaders)
    for page in range(getpages):
        resp_from_seiee_notification = seiee_session.post("https://www.seiee.sjtu.edu.cn/active/ajax_article_list.html", data={'page': str(page + 1), 'cat_id': '241', 'search_cat_code': '', 'search_cat_title': '', 'template': 'v_ajax_normal_list1'}, headers=myheaders)
        myhtml = etree.HTML(resp_from_seiee_notification.text[15:-1].encode('latin1').decode('unicode_escape').replace("\/", "/"))
        sections = myhtml.xpath("//li")
        for notice in sections:
            seieeNotification.objects.create(name=notice.xpath(".//div[@class='name']")[0].text.strip(), date=notice.xpath(".//span")[0].text.strip() + "-" + notice.xpath(".//p")[0].text.strip(), href=notice.xpath(".//a")[0].get('href'))
    lock.release()


def validate_account(username, password):
    canvas_login_url = 'https://oc.sjtu.edu.cn/login/canvas'
    myheaders_for_oc = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "oc.sjtu.edu.cn"}
    oc_session = requests.Session()
    oc_session.get(canvas_login_url, headers=myheaders_for_oc)
    resp_from_openid_connect = oc_session.get("https://oc.sjtu.edu.cn/login/openid_connect", headers=myheaders_for_oc, allow_redirects=False)
    msg, type = auto_jaccount_authorize(resp_from_openid_connect.headers['Location'], username, password)
    print()
    if type == 0 or type == 1:
        return False, msg
    else:
        lock_cookies.acquire()
        save_cookies(username, msg)
        lock_cookies.release()
        return True, "Success"


def save_collection(user, site, data):
    kwargs = {'user': user, 'site': site}
    for i, item in enumerate(data):
        kwargs['data' + str(i)] = data[item]
    obj, created = collection.objects.get_or_create(**kwargs)
    if created:
        print("already collected this one")


def delete_collection(user, site, data):
    kwargs = {'user': user, 'site': site}
    for i, item in enumerate(data):
        kwargs['data' + str(i)] = data[item]
    if site == 'weibo':
        kwargs.pop('data1')
        kwargs.pop('data2')
    collection.objects.filter(**kwargs).delete()


def get_today_regular():
    zhihu_sample = list(zhihu.objects.values('title','href').first().values())
    bilibili_sample = list(bilibili.objects.values('title','link').first().values())
    weibo_sample = list(weibo.objects.values('title','link').first().values())
    github_sample = list(github.objects.values('title','href').first().values())
    return zhihu_sample, bilibili_sample, weibo_sample, github_sample


def get_today_SJTU(jaccountname=None):
    if not jaccountname:
        return ['登录后显示','/canvas'], ['登录后显示','/dekt'],[ '登录后显示','/seiee'], ['登录后显示','/shuiyuan'],None
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    query = "SHOW TABLES LIKE %s"
    cursor.execute(query, ('canvas_' + jaccountname))
    result = cursor.fetchone()
    if result:
        # 表存在，执行查询操作
        sql_canvas = "select * from `{}` where submit = 'false'".format('canvas_' + jaccountname)
        lock_canvas.acquire()
        cursor.execute(sql_canvas)
        row_canvas = cursor.fetchone()
        lock_canvas.release()
        if row_canvas is not None:
            row_canvas = [row_canvas[4] + ": " + row_canvas[6] + "  Due at:" + row_canvas[1],row_canvas[7]]
        else:
            row_canvas=['尚未加载，刷新后即可显示',"/canvas"]
    else:
        row_canvas = ['尚未加载，刷新后即可显示',"/canvas"]

    cursor.execute(query, ('shuiyuan_' + jaccountname))
    result = cursor.fetchone()
    if result:
        sql_shuiyuan = "select * from `{}`".format('shuiyuan_' + jaccountname)
        lock_shuiyuan.acquire()
        cursor.execute(sql_shuiyuan)
        row_shuiyuan = cursor.fetchall()
        lock_shuiyuan.release()
        if row_shuiyuan is not None:
            row_shuiyuan_random_index = random.randint(0, len(row_shuiyuan) - 1)
            row_shuiyuan = row_shuiyuan[row_shuiyuan_random_index]
            row_shuiyuan = ["[" + row_shuiyuan[6] + "]" + row_shuiyuan[2],row_shuiyuan[1]]
        else:
            row_shuiyuan = ['尚未加载，刷新后即可显示',"/shuiyuan"]
    else:
        row_shuiyuan = ['尚未加载，刷新后即可显示',"/shuiyuan"]

    lock_dekt.acquire()
    row_dekt = dektinfo.objects.values('activity_name', 'active_start_time','category_url')
    lock_dekt.release()
    if len(row_dekt)==0:
        row_dekt=['尚未加载，刷新后即可显示',"/dekt"]
    else:
        row_dekt_random_index = random.randint(0, len(row_dekt) - 1)
        row_dekt = [row_dekt[row_dekt_random_index]['activity_name'] + "开始时间：" + row_dekt[row_dekt_random_index]['active_start_time'],row_dekt[row_dekt_random_index]['category_url']]

    lock_seiee.acquire()
    row_seiee = list(seieeNotification.objects.values('name','href').first().values())
    lock_seiee.release()
    if not row_seiee:
        row_seiee=['尚未加载，刷新后即可显示',"/seiee"]

    cursor.execute(query, ('calendar_' + jaccountname))
    result = cursor.fetchone()
    if result:
        data_list = gpt_filter("calendar_{}".format(jaccountname), lock=lock_calendar)
        tablesid = transfer_from_database_to_list('tablesid_' + jaccountname)
        if data_list is None:
            tablesid=[]
    else:
        data_list = None
        tablesid = []


    return row_canvas, row_dekt, row_seiee, row_shuiyuan, data_list, tablesid


def getkeyword(username, type, add=False, userkeywords=None):
    lock_keywords.acquire()
    if userkeywords:
        if add:
            if keywords.objects.filter(username=username, type=type):
                keywords.objects.filter(username=username, type=type).delete()
            for keyword in userkeywords:
                keywords.objects.create(username=username, key=keyword, type=type)
            lock_keywords.release()
            return
        lock_keywords.release()
        print("不合适的调用方法")
        return
    if type == 'all':
        result = keywords.objects.filter(username=username).all()
    else:
        result = keywords.objects.filter(username=username, type=type).all()
    lock_keywords.release()
    result = [row.key for row in result]
    return result


def erase_SJTU_user(jaccountname):
    db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
    cursor = db.cursor()
    erase_SJTU_user_query = """
            DROP TABLE `calendar_{}`,`canvas_{}`,`cookies_{}`,`cookies_{}store`,`shuiyuan_{}`,`tablesid_{}`;
            """.format(jaccountname, jaccountname, jaccountname, jaccountname, jaccountname, jaccountname)
    cursor.execute(erase_SJTU_user_query)
    db.commit()
    cursor.close()
    db.close()


zhihu_cookie = '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'
if __name__ == '__main__':
    gpt_filter('seiee_notion', lock=lock_seiee)

    print("over")
