import requests
import openai
import pandas as pd
import re
from lxml import etree
from time import time
from requests.adapters import HTTPAdapter
from PIL import Image, ImageEnhance
import pytesseract
from credential import login, re_search, get_timestamp
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import html

openai.api_key = "sk-NzVkxZUYP9aHqeUbkSxAGvfUgn5vzsPKANnG1UHR3YMa1XLp"
openai.api_base = "https://api.chatanywhere.com.cn/v1"


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


def get_github_trending():
    github_url = 'https://github.com/trending'
    rst = []
    response = requests.get(github_url)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath("//article[@class='Box-row']")
    for repository in sections:
        author = repository.xpath("./h2/a/span//text()")[0].strip()[:-2]
        title = repository.xpath("./h2/a/text()")[-1].strip()
        if len(repository.xpath("./p/text()")):
            description = repository.xpath("./p/text()")[0].strip()
        else:
            description="/"
        href = "https://github.com" + repository.xpath("./h2/a/@href")[0]
        print(author, title, description, href)
        rst.append([author, title, description, href])
    pd.DataFrame(columns=['author', 'title', 'description', 'href'], data=rst).to_csv('githubTrending.csv')


def get_zhihu_hot_topic(cookie):
    zhihu_url = 'https://www.zhihu.com/hot'
    zhihu_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127  Safari/537.36',
        'cookie': cookie
    }
    rst = []
    response = requests.get(zhihu_url, headers=zhihu_headers)
    text = response.text
    myhtml = etree.HTML(text)
    sections = myhtml.xpath("//section[@class='HotItem']")
    for question in sections:
        number = question.xpath("./div[@class='HotItem-index']//text()")[0].strip()
        title = question.xpath(".//h2[@class='HotItem-title']/text()")[0].strip()
        href = question.xpath("./div[@class='HotItem-content']/a/@href")[0].strip()
        picture_path = question.xpath("./a[@class='HotItem-img']/img")
        if picture_path:
            picture_element = etree.tostring(picture_path[0], encoding='unicode')
        else:
            picture_element = ''
        print(number, title, href, picture_element)
        rst.append([number, title, href, picture_element])
    pd.DataFrame(columns=['number', 'title', 'href', 'picture_element'], data=rst).to_csv('zhihuHotTopics.csv', encoding='gbk')


def get_bilibili_ranking():
    bilibili_url = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    rst = []
    items = requests.get(bilibili_url).json()['data']['list']
    for index, item in enumerate(items):
        rst.append([index + 1, item['pic'], item['title'], item['tname'], item['short_link_v2']])
        print(index + 1, item['pic'], item['title'], item['tname'], item['short_link_v2'])
    pd.DataFrame(columns=['rank', 'pic_href', 'title', 'tname', 'link'], data=rst).to_csv('bilibiliRanking.csv')


def get_gold_price():
    pass


def gpt_filter(site, cue=None):
    if site == "zhihu":
        if cue is None:
            cue = "娱乐新闻、政治新闻、假想性话题、与中国相关的话题"
        current_topics = pd.read_csv('zhihuHotTopics.csv', encoding='gbk')
        topics = ""
        for i in current_topics.values:
            topics += '（' + str(i[1]) + '） ' + i[2] + '；'
        messages = [{'role': 'user', 'content': f'我现在在进行话题筛选，我希望关注{cue}，请在我接下来给出的若干带编号的话题中选出符合我提出的标准中任一条的话题，将筛选后的话题的编号进行输出。话题如下：{topics}'}, ]
        ans = gpt_35_api_stream(messages)
        if ans[0] != True:
            print("gpt调用异常！！！！！", ans)
            return 0
        else:
            numbers = [int(num) for num in re.split('[，；。、,.]', ans[1]) if num.strip().isdigit()]
            content = []
            for index in numbers:
                content.append([current_topics['number'][index - 1], current_topics['title'][index - 1], current_topics['href'][index - 1], current_topics['picture_element'][index - 1]])

            return content


def get_weibo_hot_topic():
    weibo_url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
    rst = []
    items = requests.get(weibo_url).json()['data']['cards'][0]['card_group']
    for index, item in enumerate(items):
        rst.append([item['pic'], item['desc'], item['scheme']])
        print([item['pic'], item['desc'], item['scheme']])
    pd.DataFrame(columns=['rank_pic_href', 'title', 'link'], data=rst).to_csv('weiboRanking.csv')


'''*************SJTU板块*************'''


def autocaptcha(path):
    """Auto identify captcha in path.

    Use pytesseract to identify captcha.

    Args:
        path: string, image path.

    Returns:
        string, OCR identified code.
    """
    im = Image.open(path)

    im = im.convert('L')
    im = ImageEnhance.Contrast(im)
    im = im.enhance(3)
    img2 = Image.new('RGB', (150, 60), (255, 255, 255))
    img2.paste(im.copy(), (25, 10))

    # TODO: add auto environment detect
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

    """*************************** G A ******************************"""
    print("Starting GA......")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    url = "https://www.google-analytics.com/analytics.js"
    driver.get(url)
    print("GA get url......")
    analytics_script = driver.execute_script("return document.documentElement.innerHTML")
    decoded_code = html.unescape(analytics_script)
    modified_script = decoded_code[125:-14] + "\nga('create', 'UA-XXXX-Y');"
    driver.execute_script(modified_script)
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'], path=cookie['path'])
    session.cookies.set('_gat', "1")
    driver.quit()
    """*************************** G A ******************************"""
    return session, data


def dekt():
    username = input('Username: ')
    password = input('Password: ')
    dekt_login_url = 'https://jaccount.sjtu.edu.cn/oauth2/authorize?response_type=code&client_id=sowyD3hGhP6f6O92bevg&redirect_uri=https://dekt.sjtu.edu.cn/h5/index&state=&scope=basic'
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    dekt_session = requests.Session()
    resp_from_oauth_start = dekt_session.get(dekt_login_url, headers=myheaders)
    dekt_session, data = process_captcha_and_GA(resp_from_oauth_start, dekt_session, username, password)
    resp = dekt_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data)

    print(resp.text)
    return 1


def canvas():
    username = input('Username: ')
    password = input('Password: ')
    canvas_login_url = 'https://oc.sjtu.edu.cn/login/canvas'
    myheaders_for_oc = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "oc.sjtu.edu.cn"}
    oc_session = requests.Session()
    oc_session.get(canvas_login_url, headers=myheaders_for_oc)

    resp_from_openid_connect = oc_session.get("https://oc.sjtu.edu.cn/login/openid_connect", headers=myheaders_for_oc, allow_redirects=False)
    myheaders_for_oauth = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    oauth_session = requests.Session()
    resp_from_oauth = oauth_session.get(resp_from_openid_connect.headers['Location'], headers=myheaders_for_oauth)

    oauth_session, data = process_captcha_and_GA(resp_from_oauth, oauth_session, username, password)

    # site_sum_cookie = "GS"
    # site_sum_cookie_name="_ga_QP6YR9D8CK"
    # for cookie in oc_session.cookies:
    #     if cookie.name == '_gid':
    #         site_sum_cookie+=cookie.value[2:6]
    #         site_sum_cookie+=cookie.value[17:27]
    #         site_sum_cookie+=".1.0."
    #         site_sum_cookie+=cookie.value[17:27]
    #         site_sum_cookie+=".0.0.0"
    #         oc_session.cookies.set(site_sum_cookie_name, site_sum_cookie)
    #         break

    resp_from_ulogin = oauth_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', headers=myheaders_for_oauth, data=data, allow_redirects=False)
    resp_from_jalogin = oauth_session.get("https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
    resp_from_oauth2_authorize = oauth_session.get(resp_from_jalogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
    oc_session.cookies.update(oauth_session.cookies)
    resp_from_oc = oc_session.get(resp_from_oauth2_authorize.headers['Location'], headers=myheaders_for_oc)
    _debug_show_resp(resp_from_oc)
    print(resp_from_oc.text)


zhihu_cookie = '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'
if __name__ == '__main__':
    # get_github_trending()
    # get_zhihu_hot_topic(zhihu_cookie)
    # get_bilibili_ranking()
    # get_gold_price()
    # print(gpt_filter('zhihu'))
    # get_weibo_hot_topic()
    # dekt()
    canvas()
    print("over")
