import requests
import openai
import pandas as pd
import re
from lxml import etree
from time import time,localtime,strftime,mktime, strptime
from PIL import Image, ImageEnhance
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os
# from app01.models import  UserInfo,collection,zhihu,github,bilibili,weibo,dektinfo
openai.api_key = "sk-NzVkxZUYP9aHqeUbkSxAGvfUgn5vzsPKANnG1UHR3YMa1XLp"
openai.api_base = "https://api.chatanywhere.com.cn/v1"
from app01.models import *

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
def get_github_trending():
    github_url = 'https://github.com/trending'
    rst = []
    response = requests.get(github_url)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath("//article[@class='Box-row']")
    github.objects.all().delete()
    for repository in sections:
        author = repository.xpath("./h2/a/span//text()")[0].strip()[:-2]
        title = repository.xpath("./h2/a/text()")[-1].strip()
        if len(repository.xpath("./p/text()"))>0:
            description = repository.xpath("./p/text()")[0].strip()
        else:
            description ="A repository"
        href = "https://github.com" + repository.xpath("./h2/a/@href")[0]
        # print(author, title, description, href)
        # rst.append([author, title, description, href])
        github.objects.create(author=author,title=title,description=description,href=href)
    # pd.DataFrame(columns=['author', 'title', 'description', 'href'], data=rst).to_csv('githubTrending.csv')


def get_zhihu_hot_topic(cookie):
    zhihu_url = 'https://www.zhihu.com/hot'
    zhihu_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Kmyhtml, like Gecko) Chrome/113.0.5672.127  Safari/537.36',
        'cookie': cookie
    }
    rst = []
    response = requests.get(zhihu_url, headers=zhihu_headers)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath("//section[@class='HotItem']")
    zhihu.objects.all().delete()
    for question in sections:
        number = question.xpath("./div[@class='HotItem-index']//text()")[0].strip()
        title = question.xpath(".//h2[@class='HotItem-title']/text()")[0].strip()
        href = question.xpath("./div[@class='HotItem-content']/a/@href")[0].strip()
        picture_path = question.xpath("./a[@class='HotItem-img']/img")
        if picture_path:
            picture_element = etree.tostring(picture_path[0], encoding='unicode')
        else:
            picture_element = ''
        # print(number, title, href, picture_element)
        zhihu.objects.create(number=number,title=title,href=href,picture_element=picture_element)
        # rst.append([number, title, href, picture_element])
    # pd.DataFrame(columns=['number', 'title', 'href', 'picture_element'], data=rst).to_csv('zhihuHotTopics.csv', encoding='gbk')


def get_bilibili_ranking():
    bilibili_url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    rst = []
    items = requests.get(bilibili_url).json()['data']['list']
    bilibili.objects.all().delete()
    for index, item in enumerate(items):
        bilibili.objects.create(rank=index+1,pic_href=item['pic'],title=item['title'],tname=item['tname'],link=item['short_link_v2'])
    #     rst.append([index + 1, item['pic'], item['title'], item['tname'], item['short_link_v2']])
    #     print(index + 1, item['pic'], item['title'], item['tname'], item['short_link_v2'])
    # pd.DataFrame(columns=['rank', 'pic_href', 'title', 'tname', 'link'], data=rst).to_csv('bilibiliRanking.csv')


def get_gold_price():
    pass


def gpt_filter(site, cue=None):
    if site == "zhihu":
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        # current_topics = pd.read_csv('zhihuHotTopics.csv', encoding='gbk')
        current_topics = zhihu.objects.all()
        topics = ""
        for a in current_topics:
            topics += '（' + a.number + '） ' + a.title + '；'
        messages = [{'role': 'user', 'content': f'我现在在进行话题筛选，我希望关注{cue}，请在我接下来给出的若干带编号的话题中选出符合我提出的标准中任一条的话题，将筛选后的话题的编号进行输出。话题如下：{topics}'}, ]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return 0
        else:
            content = []
            numbers = [int(num) for num in re.split('[，；。、,.]', ans[1]) if num.strip().isdigit()]
            for index in numbers:
                content.append([current_topics[index - 1].number, current_topics[index - 1].title, current_topics[index - 1].href, current_topics[index - 1].picture_element])
            return content
    elif site == 'github':
        if cue is None:
            cue = "与python相关的"
        current_topics = github.objects.all()
        topics = ""
        i=1
        for a in current_topics:
            topics += '('+str(i)+') '+a.title + '；'
            i=i+1
        messages = [{'role': 'user', 'content': f'我现在在进行话题筛选，我希望关注{cue}，请在我接下来给出的若干带编号的话题中选出符合我提出的标准中任一条的话题，将筛选后的话题的编号进行输出。话题如下：{topics}'}, ]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return 0
        else:
            content = []
            # numbers = [int(num) for num in re.split('[，；。、,.]', ans[1]) if num.strip().isdigit()]
            numbers = [int(match.group(1)) for match in re.finditer(r'\((\d+)\)', ans[1])]
            for index in numbers:
                content.append([current_topics[index - 1].author, current_topics[index - 1].title, current_topics[index - 1].description, current_topics[index - 1].href])
            return content
    elif site == 'bilibili':
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        current_topics = bilibili.objects.all()
        topics = ""

        for a in current_topics:
            topics += '('+str(a.rank)+') '+a.tname + '；'
        print(topics)
        messages = [{'role': 'user', 'content': f'我现在在进行话题筛选，我希望关注{cue}，请在我接下来给出的若干带编号的话题中选出符合我提出的标准中任一条的话题，将筛选后的话题的编号进行输出,编号时不要加括号。话题如下：{topics}'}, ]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return 0
        else:
            content = []
            numbers = [int(num) for num in re.split('[，；。、,.]', ans[1]) if num.strip().isdigit()]
            # numbers = [int(match.group(1)) for match in re.finditer(r'\((\d+)\)', ans[1])]
            for index in numbers:
                content.append([current_topics[index - 1].rank, current_topics[index - 1].title, current_topics[index - 1].tname, current_topics[index - 1].pic_href,current_topics[index-1].link])
            return content
    elif site == 'weibo':
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        current_topics = weibo.objects.all()
        topics = ""
        i=1
        for a in current_topics:
            topics += '('+str(i)+') '+a.title + '；'
            i+=1
        print(topics)
        messages = [{'role': 'user', 'content': f'我现在在进行话题筛选，我希望关注{cue}，请在我接下来给出的若干带编号的话题中选出符合我提出的标准中任一条的话题，将筛选后的话题的编号进行输出,编号时不要加括号。话题如下：{topics}'}, ]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return 0
        else:
            content = []
            numbers = [int(num) for num in re.split('[，；。、,.]', ans[1]) if num.strip().isdigit()]
            # numbers = [int(match.group(1)) for match in re.finditer(r'\((\d+)\)', ans[1])]
            for index in numbers:
                content.append([current_topics[index - 1].title, current_topics[index - 1].rank_pic_href, current_topics[index-1].link])
            return content
    elif 'shuiyuan' in site:
        if cue is None:
            cue = "学业考试相关，八卦相关的"
        topics = ""
        current_topics=[]
        db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', port=3306, db='nis3368')
        # 使用cursor()方法获取操作游标
        cursor = db.cursor()
        sql = "select * from `{}`".format(site)
        # 4.执行sql语句
        cursor.execute(sql)
        i = 1
        while True:
            row = cursor.fetchone()
            if not row:
                break
            topics += '(' + str(i) + ') ' + row[1] + '；'
            current_topics.append(row)
            i+=1
        topics=topics.encode('utf-8')
        print(topics)
        messages = [{'role': 'user', 'content': f'我现在在进行话题筛选，我希望关注{cue}，请在我接下来给出的若干带编号的话题中选出符合我提出的标准中任一条的话题，将筛选后的话题的编号进行输出,编号时不要加括号。话题如下：{topics}'}, ]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return 0
        else:
            content = []
            numbers = [int(num) for num in re.split('[，；。、,.]', ans[1]) if num.strip().isdigit()]
            # numbers = [int(match.group(1)) for match in re.finditer(r'\((\d+)\)', ans[1])]
            for index in numbers:
                content.append([current_topics[index - 1][0], current_topics[index - 1][1], current_topics[index-1][2], current_topics[index-1][3], current_topics[index-1][4], current_topics[index-1][5], current_topics[index-1][6], current_topics[index-1][7], current_topics[index-1][8]])
            return content

def get_weibo_hot_topic():
    weibo_url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
    rst = []
    items = requests.get(weibo_url).json()['data']['cards'][0]['card_group']
    weibo.objects.all().delete()
    for index, item in enumerate(items):
        weibo.objects.create(rank_pic_href=item['pic'],title=item['desc'],link=item['scheme'])
    #     rst.append([item['pic'], item['desc'], item['scheme']])
    #     print([item['pic'], item['desc'], item['scheme']])
    # pd.DataFrame(columns=['rank_pic_href', 'title', 'link'], data=rst).to_csv('weiboRanking.csv')


def get_minhang_24h_weather():
    minhang_weather_url="https://www.tianqi.com/minhang/"
    myheaders = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127  Safari/537.36'}
    response=requests.get(minhang_weather_url,headers=myheaders)
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
    weather_pics_path = './weather_pics'
    existing_weather_pics = os.listdir(weather_pics_path)
    rst=[[],[],[],[],[],[]]    # 依次为该小时的 已保存到本地的天气图片的名称，天气文字，气温，风向，风力，小时
    sections = myhtml.xpath("//div[@class='twty_hour']/div/div")
    for item in sections:
        for pic in item.xpath("./ul[1]/li"):
            pic_url=pic.xpath("./img/@src")[0]
            pic_name=re.search(r'\/([^\/]*)$', pic_url).group(1)
            if pic_name not in existing_weather_pics:
                response = requests.get("https:"+pic_url, headers=weather_pic_headers)
                if response.status_code == 200:
                    with open('./weather_pics/'+pic_name, 'wb') as file:
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
    reformed_rst=[[rst[0][i],rst[1][i],rst[2][i],rst[3][i],rst[4][i],rst[5][i]]for i in range(len(rst[0]))]
    for i in range(len(rst[0])):
        minhang_24h_weather.objects.create(Name_of_weather_picture=rst[0][i],weather_text=rst[1][i],temperature=rst[2][i],wind_direction=rst[3][i],wind_strength=rst[4][i],hour=rst[5][i])



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
            resp_from_jalogin = oauth_session.get("https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            resp_from_oauth2_authorize = oauth_session.get(resp_from_jalogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            break
        except Exception:
            print("oops!retrying...")
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
    for cookie in GA_cookie:
        session.cookies.set(cookie['name'], cookie['value'], path=cookie['path'])
    session.cookies.set('_gat', "1")

    return session, data
    """*************************** G A ******************************"""
global_GA_cookie = None

def _get_GA():
    global global_GA_cookie
    if global_GA_cookie is not None:
        pass
    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        url = "https://www.google-analytics.com/analytics.js"
        driver.get(url)
        # analytics_script = driver.execute_script("return document.documentElement.innerHTML")
        # decoded_code = html.unescape(analytics_script)
        # modified_script = decoded_code[125:-14] + "\nga('create', 'UA-XXXX-Y');"
        # driver.execute_script(modified_script)
        with open("js/GA.js", "r") as GA:
            print("executing GA ......")
            driver.execute_script(GA.read())
        global_GA_cookie = driver.get_cookies()
        global_GA_cookie.append({'name': '_ga_QP6YR9D8CK', 'path': '/', 'value': "GS1.3." + str(int(time())) + ".31.0." + str(int(time())) + ".0.0.0"})
        driver.quit()
    return global_GA_cookie
def dekt():
    username = input('Username: ')
    password = input('Password: ')
    dekt_login_url = 'https://jaccount.sjtu.edu.cn/oauth2/authorize?response_type=code&client_id=sowyD3hGhP6f6O92bevg&redirect_uri=https://dekt.sjtu.edu.cn/h5/index&state=&scope=basic'
    myheaders_for_dekt = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "dekt.sjtu.edu.cn"}
    oauth_session_cookies, jump_url = auto_jaccount_authorize(dekt_login_url, username, password)
    dekt_session = requests.Session()
    dekt_session.cookies.update(oauth_session_cookies)
    myheaders_for_dekt['Content-Type'] = "application/json"
    resp_from_dekt = dekt_session.post("https://dekt.sjtu.edu.cn/api/auth/secondclass/loginByJa?time=" + str(round(time() * 1000)) + "&publicaccountid=sjtuvirtual", headers=myheaders_for_dekt,
                                       data=json.dumps({"code": jump_url[39:], "redirect_uri": "https://dekt.sjtu.edu.cn/h5/index", "scope": "basic", "client_id": "sowyD3hGhP6f6O92bevg", "publicaccountid": "sjtuvirtual"}))
    token = resp_from_dekt.json()['data']['token']
    myheaders_for_dekt.update({'Jtoken': resp_from_dekt.json()['data']['jtoken'], 'Curuserid': "null"})
    rst = []
    resp_from_hszl = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 0, "redTour": 1}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_hszl.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="红色之旅", item_id=str(item['id']), activity_name=item['activityName'], enroll_start_time=enrollStartTime, enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeStartTime'] / 1000)
                                                                                                                                                                     ), active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                                                                                                                                                 ), activity_picurl=item['activityPicurl'])
    resp_from_ldjy = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 1, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_ldjy.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="劳动教育", item_id=str(item['id']),activity_name=item['activityName'], enroll_start_time=enrollStartTime, enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                                                             ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeStartTime'] / 1000)
                                                                                                         ), active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                                                                                     ), activity_picurl=item['activityPicurl'])
    resp_from_zygy = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "zygy", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_zygy.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="志愿公益", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_wthd = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "yshd", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_wthd.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="文体活动", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_kjcx = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "kjcx", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_kjcx.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="科技创新", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_jtjz = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "jtjz", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_jtjz.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="讲坛讲座", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_qt = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                     data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "qt", "topicCode": "", "statusType": "1", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_qt.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="其他", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_hszl = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 0, "redTour": 1}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_hszl.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="红色之旅", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_ldjy = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 1, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_ldjy.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="劳动教育", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_zygy = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "zygy", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_zygy.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="志愿教育", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_wthd = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "yshd", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_wthd.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="文体活动", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_kjcx = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "kjcx", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_kjcx.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="科技创新", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_jtjz = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                       data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "jtjz", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_jtjz.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="讲坛讲座", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])
    resp_from_qt = dekt_session.post("https://dekt.sjtu.edu.cn/api/wmt/secondclass/fmGetActivityByPage?time=" + str(round(time() * 1000)) + "&tenantId=500&token=" + token + "&publicaccount", headers=myheaders_for_dekt,
                                     data=json.dumps({"sort": "id", "order": "desc", "offset": 0, "limit": 50, "queryParams": {"activityName": "", "categoryCode": "qt", "topicCode": "", "statusType": "2", "orderType": 1, "laborEducation": 0, "redTour": 0}, "publicaccountid": "sjtuvirtual"}))
    for item in resp_from_qt.json()['rows']:
        if item['enrollStartTime'] is not None:
            enrollStartTime = strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollStartTime'] / 1000))
        else:
            enrollStartTime = "/"
        dektinfo.objects.create(category="其他", item_id=str(item['id']), activity_name=item['activityName'],
                                enroll_start_time=enrollStartTime,
                                enroll_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['enrollEndTime'] / 1000)
                                                         ), active_start_time=strftime('%Y-%m-%d %H:%M:%S', localtime(
                item['activeStartTime'] / 1000)
                                                                                       ),
                                active_end_time=strftime('%Y-%m-%d %H:%M:%S', localtime(item['activeEndTime'] / 1000)
                                                         ), activity_picurl=item['activityPicurl'])

    return 1

def canvas():
    try:
        df = pd.read_csv('course_id_name_dict.csv')
        course_id_name_dict = df.set_index(df.columns[0]).to_dict()[df.columns[1]]
    except FileNotFoundError:
        course_id_name_dict = {}
    username = input('Username: ')
    password = input('Password: ')
    canvas_login_url = 'https://oc.sjtu.edu.cn/login/canvas'
    myheaders_for_oc = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "oc.sjtu.edu.cn"}
    oc_session = requests.Session()
    if global_GA_cookie is not None:
        for cookie in global_GA_cookie:
            oc_session.cookies.set_cookie(cookie['name'], cookie['value'], path=cookie['path'])
    oc_session.get(canvas_login_url, headers=myheaders_for_oc)

    resp_from_openid_connect = oc_session.get("https://oc.sjtu.edu.cn/login/openid_connect", headers=myheaders_for_oc, allow_redirects=False)
    oauth_session_cookies, jump_url = auto_jaccount_authorize(resp_from_openid_connect.headers['Location'], username, password)

    oc_session.cookies.update(oauth_session_cookies)
    resp_from_oc = oc_session.get(jump_url, headers=myheaders_for_oc)
    planner_data = oc_session.get("https://oc.sjtu.edu.cn/api/v1/planner/items?start_date=" + strftime("%Y-%m-%d", localtime(time() + (-7 * 24 * 60 * 60))) + "&order=asc&per_page=100", headers=myheaders_for_oc)

    json_data = json.loads(planner_data.text[9:])
    rst = []
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
        rst.append([due_at, submit, item['plannable_id'], course_id_name_dict[item['course_id']], descript, name, item['plannable']['html_url']])
    rst = sorted(rst, key=lambda x: x[0])
    pd.DataFrame.from_dict(course_id_name_dict, orient='index').to_csv('course_id_name_dict.csv')
    pd.DataFrame(columns=['due_time', 'submission_status', 'id', 'course_name', 'description', 'name', 'url'], data=rst).to_csv("PERSONAL_canvas.csv")
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


def shuiyuan():
    username = input('Username: ')
    password = input('Password: ')
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

    oauth_session_cookies, jump_url = auto_jaccount_authorize(resp_from_auth_jaccount.headers['Location'], username, password)

    shuiyuan_session.cookies.update(oauth_session_cookies)
    resp_from_shuiyuan = shuiyuan_session.get(jump_url, headers=myheaders_for_shuiyuan)
    resp_from_latest = shuiyuan_session.get("https://shuiyuan.sjtu.edu.cn/latest.json?ascending=false", headers=default_headers)
    infos = resp_from_latest.json()['topic_list']['topics']
    create_dynamic_model_shuiyuan(username)
    for index, item in enumerate(infos):
        ref = "https://shuiyuan.sjtu.edu.cn/t/topic/" + str(item['id'])
        if 'last_read_post_number' in item:
            ref += '/' + str(item['last_read_post_number'])
        insert_dynamic_model_shuiyuan(table_name=username,ref=ref, title=item['title'],posts_count= item['posts_count'], reply_count=item['reply_count'], unseen=item['unseen'], shuiyuan_category_dict=shuiyuan_category_dict[str(item['category_id'])],tags=item['tags'], views=item['views'])
    # 仅当category字典需要更新时才调用此函数
    # update_shuiyuan_category(shuiyuan_session,default_headers)
    print("shuiyuan success!!!")
    return 1

def mysjtu_calendar(beginfrom=0, endat=7):  # beginfrom和endat均是相对今天而言
    username = input('Username: ')
    password = input('Password: ')
    mysjtu_url = "https://my.sjtu.edu.cn/ui/calendar/"
    default_headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "my.sjtu.edu.cn"}
    mysjtu_session = requests.Session()
    resp_from_mysjtu = mysjtu_session.get(mysjtu_url, headers=default_headers, allow_redirects=False)
    resp_from_mysjtu = mysjtu_session.get("https://my.sjtu.edu.cn" + resp_from_mysjtu.headers['Location'], headers=default_headers, allow_redirects=False)
    oauth_session = requests.Session()
    myheaders_for_oauth = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    while True:
        try:
            resp_from_oauth = oauth_session.get(resp_from_mysjtu.headers['Location'], headers=myheaders_for_oauth)
            oauth_session, data = process_captcha_and_GA(resp_from_oauth, oauth_session, username, password)
            resp_from_ulogin = oauth_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', headers=myheaders_for_oauth, data=data, allow_redirects=False)
            resp_from_jalogin = oauth_session.get("https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            resp_from_oauth2_authorize = oauth_session.get(resp_from_jalogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            break
        except Exception:
            print("oops!retrying...")
            continue
    mysjtu_session.cookies.update(oauth_session.cookies)
    mysjtu_session.get(resp_from_oauth2_authorize.headers['Location'], headers=default_headers)

    calendar_session = requests.Session()
    calendar_session.cookies.update((mysjtu_session.cookies))
    calendar_headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "calendar.sjtu.edu.cn"}
    aa = calendar_session.get("https://calendar.sjtu.edu.cn/?tenantUserId=" + username, headers=calendar_headers, allow_redirects=False)
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
    next_week_calendar_url = "https://calendar.sjtu.edu.cn/api/event/list?startDate=" + strftime("%Y-%m-%d", localtime(time() + (beginfrom * 24 * 60 * 60))) + "+00:00&endDate=" + strftime("%Y-%m-%d", localtime(time() + (endat * 24 * 60 * 60))) + "+00:00&weekly=false&ids="
    calendar_list = calendar_session.get(next_week_calendar_url, headers=calendar_headers)
    create_dynamic_model_calendar(username)
    for event in calendar_list.json()['data']['events']:
        insert_dynamic_model_calendar(table_name=username,title=event["title"],starttime=event["startTime"],endtime=event["endTime"],location=event["location"],json_detail_url="https://calendar.sjtu.edu.cn/api/event/detail?id=" + event['eventId'])
    print("calendar success!!!")
    return calendar_session.cookies

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
    schedule_data = {"allDay": allDay, "body": description, "endTime": endTime, "importance": "LOW", "location": location, "reminderMinutes": reminderMinutes, "recurrence": recurrence, "status": status, "recurrenceEndDate": "", "startTime": startTime, "title": title, "extremity": False}
    if schedule_type == "课程":
        schedule_data['calendarId'] = "67fb2fa3-c3bf-46e0-99be-2e07ea2725b7"
    elif schedule_type == "会议":
        schedule_data['calendarId'] = "b469c560-cd67-47f4-8c15-22684a3eb71d"
    elif schedule_type == "私人":
        schedule_data['calendarId'] = "028bac3d-5032-45ce-bcf5-a4da21a28cb1"
    else:
        print("日程种类错误")
        return 0
    if reminderMinutes == -1:
        schedule_data['reminderOn'] = False
    else:
        schedule_data['reminderOn'] = True
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "calendar.sjtu.edu.cn", 'Content-Type': "application/json;charset=UTF-8"}
    resp = requests.post("https://calendar.sjtu.edu.cn/api/event/create", headers=myheaders, data=json.dumps(schedule_data), cookies=required_cookies, allow_redirects=False).json()
    if resp['success'] != True:
        print("Creation failure due to", resp['msg'])
        return 0
    else:
        print("Create schedule success!")


def seiee_notification(getpages=1):
    seiee_url = 'https://www.seiee.sjtu.edu.cn/xsgz_tzgg_xssw.html'
    rst = []
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "www.seiee.sjtu.edu.cn"}
    seiee_session = requests.Session()
    seiee_session.get(seiee_url, headers=myheaders)
    for page in range(getpages):
        resp_from_seiee_notification = seiee_session.post("https://www.seiee.sjtu.edu.cn/active/ajax_article_list.html", data={'page': str(page + 1), 'cat_id': '241', 'search_cat_code': '', 'search_cat_title': '', 'template': 'v_ajax_normal_list1'}, headers=myheaders)
        myhtml = etree.HTML(resp_from_seiee_notification.text[15:-1].encode('latin1').decode('unicode_escape').replace("\/", "/"))
        sections = myhtml.xpath("//li")
        for notice in sections:
            seieeNotification.objects.create(name=notice.xpath(".//div[@class='name']")[0].text.strip(),date= notice.xpath(".//span")[0].text.strip() + "-" + notice.xpath(".//p")[0].text.strip(),href=notice.xpath(".//a")[0].get('href'))

zhihu_cookie = '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'
if __name__ == '__main__':

    print("over")
