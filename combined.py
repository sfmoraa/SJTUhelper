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
    myhtml = etree.myhtml(text)
    sections = myhtml.xpath("//article[@class='Box-row']")
    for repository in sections:
        author = repository.xpath("./h2/a/span//text()")[0].strip()[:-2]
        title = repository.xpath("./h2/a/text()")[-1].strip()
        description = repository.xpath("./p/text()")[0].strip()
        href = "https://github.com" + repository.xpath("./h2/a/@href")[0]
        print(author, title, description, href)
        rst.append([author, title, description, href])
    pd.DataFrame(columns=['author', 'title', 'description', 'href'], data=rst).to_csv('githubTrending.csv')


def get_zhihu_hot_topic(cookie):
    zhihu_url = 'https://www.zhihu.com/hot'
    zhihu_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Kmyhtml, like Gecko) Chrome/113.0.5672.127  Safari/537.36',
        'cookie': cookie
    }
    rst = []
    response = requests.get(zhihu_url, headers=zhihu_headers)
    text = response.text
    myhtml = etree.myhtml(text)
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


def update_cookies(all_cookies, new_cookies):
    all_cookie_dict = dict_from_cookiejar(all_cookies)
    new_cookies_dict = dict_from_cookiejar(new_cookies)
    for item in new_cookies_dict:
        all_cookie_dict[str(item)] = new_cookies_dict[str(item)]

    return cookiejar_from_dict(all_cookie_dict)


def dekt():
    dekt_login_url = 'https://jaccount.sjtu.edu.cn/oauth2/authorize?response_type=code&client_id=sowyD3hGhP6f6O92bevg&redirect_uri=https://dekt.sjtu.edu.cn/h5/index&state=&scope=basic'
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Kmyhtml, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    while True:
        username = input('Username: ')
        print(1)
        password = input('Password(no echo): ')
        print(2)
        while True:
            resp_from_oauth2 = requests.get(dekt_login_url, headers=headers)
            all_cookies = resp_from_oauth2.cookies
            cookie_of_302 = resp_from_oauth2.request.headers['Cookie']
            cookie_of_302_dict = {}
            cookie_of_302_dict[cookie_of_302[:11]] = cookie_of_302[12:]
            all_cookies = update_cookies(all_cookies, cookiejar_from_dict(cookie_of_302_dict))
            _debug_show_resp(resp_from_oauth2)

            # 38

            captcha_id = re_search(r'img.src = \'captcha\?(.*)\'', resp_from_oauth2.text)
            if not captcha_id:
                print('Captcha not found! Retrying...')
                continue
            captcha_id += get_timestamp()
            captcha_url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?' + captcha_id
            captcha = requests.get(captcha_url, cookies=all_cookies, headers={'Referer': 'https://jaccount.sjtu.edu.cn/jaccount', 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Kmyhtml, like Gecko) Chrome/80.0.3987.87 Safari/537.36"})
            update_cookies(all_cookies, captcha.cookies)
            _debug_show_resp(captcha)
            # 45

            with open('captcha.jpeg', 'wb') as f:
                f.write(captcha.content)
            code = autocaptcha('captcha.jpeg').strip()

            sid = re_search(r'sid" value="(.*?)"', resp_from_oauth2.text)
            returl = re_search(r'returl" value="(.*?)"', resp_from_oauth2.text)
            se = re_search(r'se" value="(.*?)"', resp_from_oauth2.text)
            client = re_search(r'client" value="(.*?)"', resp_from_oauth2.text)
            uuid = re_search(r'captcha\?uuid=(.*?)&t=', resp_from_oauth2.text)
            if not (sid and returl and se and uuid):
                print('Params not found! Retrying...')
                continue
            data = {'sid': sid, 'returl': returl, 'se': se, 'client': client, 'user': username,
                    'pass': password, 'captcha': code, 'g-recaptcha-response': '', 'uuid': uuid}

            """*************************** G A ******************************"""
            GA_cookie = {'_gat': "1"}
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)
            url = "https://www.google-analytics.com/analytics.js"
            driver.get(url)
            analytics_script = driver.execute_script("return document.documentElement.innerHTML")
            decoded_code = html.unescape(analytics_script)
            modified_script = decoded_code[125:-14] + "\nga('create', 'UA-XXXX-Y');"
            driver.execute_script(modified_script)
            cookies = driver.get_cookies()
            for cookie in cookies:
                GA_cookie[str(cookie['name'])] = cookie['value']
            driver.quit()
            """*************************** G A ******************************"""
            # print(GA_cookie)
            all_cookies = update_cookies(all_cookies, cookiejar_from_dict(GA_cookie))

            # 不需要每次请求，返回值一定
            # sum=requests.post("https://www.google-analytics.com/j/collect?v=1&_v=j101&t=pageview&_s=1&dl="+resp_from_oauth2.request.url+"&dr=https%3A%2F%2Fdekt.sjtu.edu.cn%2F&ul=zh-cn&de=UTF-8&dt=%E4%B8%8A%E6%B5%B7%E4%BA%A4%E9%80%9A%E5%A4%A7%E5%AD%A6%E7%BB%9F%E4%B8%80%E8%BA%AB%E4%BB%BD%E8%AE%A4%E8%AF%81&tid=UA-171546692-1&_slc=1",headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36",'Referer': "https://jaccount.sjtu.edu.cn/",'Host': "www.google-analytics.com"})
            # _debug_show_resp(sum)
            # print(sum.content)
            site_sum = "QP6YR9D8CK"

            headers['referer'] = resp_from_oauth2.request.url
            headers['Origin'] = "https://jaccount.sjtu.edu.cn"
            resp_from_ulogin = requests.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', headers=headers, data=data, cookies=all_cookies, allow_redirects=False)
            _debug_show_resp(resp_from_ulogin)
            cookie_of_ulogin = resp_from_ulogin.cookies
            if 'JAAuthCookie' not in dict_from_cookiejar(cookie_of_ulogin):
                continue
            all_cookies = update_cookies(all_cookies, cookie_of_ulogin)

            jump1_url = "https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location']
            resp_from_jump1 = requests.get(jump1_url, cookies=all_cookies, headers=headers, allow_redirects=False)
            _debug_show_resp(resp_from_jump1, addition_msg="resp_from_jump1")
            cookie_of_jump1 = resp_from_jump1.cookies
            all_cookies = update_cookies(all_cookies, cookie_of_jump1)

            del headers['Origin']
            headers['Connection'] = 'close'
            all_cookies = update_cookies(all_cookies, cookiejar_from_dict({'_ga_QP6YR9D8CK': "GS" + GA_cookie['_gid'][2:6] + GA_cookie['_gid'][17:27] + ".1.0." + GA_cookie['_gid'][17:27] + ".0.0.0"}))

            jump2_url = resp_from_jump1.headers['Location']
            resp_from_jump2 = requests.get(jump2_url, cookies=all_cookies, headers=headers)  # , allow_redirects=False)
            _debug_show_resp(resp_from_jump2, addition_msg="resp_from_jump2")

            redirect_history = resp_from_jump2.history

            # 打印每个重定向的状态码和URL
            for redirect in redirect_history:
                print(f'Status Code: {redirect.status_code}')
                print(f'Redirect URL: {redirect.url}')
                print(redirect.headers)
                print('---')

            # cookie_of_jump2 = resp_from_jump2.cookies
            # all_cookies = update_cookies(all_cookies, cookie_of_jump2)
            #
            # jump3_url = resp_from_jump2.headers['Location']
            # resp_from_jump3 = requests.get(jump3_url, headers=headers, cookies=all_cookies, allow_redirects=False)
            # _debug_show_resp(resp_from_jump3, addition_msg="resp_from_jump3")
            # cookie_of_jump3 = resp_from_jump3.cookies
            # all_cookies = update_cookies(all_cookies, cookie_of_jump3)
            #
            # jump4_url = resp_from_jump3.headers['Location']
            # resp_from_jump4 = requests.get(jump4_url, headers=headers, allow_redirects=False)
            # _debug_show_resp(resp_from_jump4, addition_msg="resp_from_jump4")
            # cookie_of_jump4 = resp_from_jump4.cookies
            # all_cookies = update_cookies(all_cookies, cookie_of_jump4)
            #
            # jump5_url = resp_from_jump4.headers['Location']
            # resp_from_jump5 = requests.get(jump5_url, headers=headers, allow_redirects=False)
            # _debug_show_resp(resp_from_jump5, addition_msg="resp_from_jump5")
            # cookie_of_jump5 = resp_from_jump5.cookies
            # all_cookies = update_cookies(all_cookies, cookie_of_jump5)
            #
            # jump6_url = resp_from_jump5.headers['Location']
            # resp_from_jump6 = requests.get(jump6_url, cookies=all_cookies, headers=headers)
            # _debug_show_resp(resp_from_jump6, addition_msg="resp_from_jump6")

            return 1


def canvas():
    canvas_login_url = 'https://oc.sjtu.edu.cn/login/canvas'
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "oc.sjtu.edu.cn"}
    while True:
        username = input('Username: ')
        password = input('Password: ')
        while True:
            resp_from_homepage = requests.get(canvas_login_url, headers=myheaders)
            all_cookies = resp_from_homepage.cookies
            _debug_show_resp(resp_from_homepage, addition_msg="(1)")

            resp_from_openidconnect = requests.get("https://oc.sjtu.edu.cn/login/openid_connect", headers=myheaders, cookies=all_cookies, allow_redirects=False)
            _debug_show_resp(resp_from_openidconnect, addition_msg="(2)")
            all_cookies = update_cookies(all_cookies, resp_from_openidconnect.cookies)

            myheaders['Host'] = 'jaccount.sjtu.edu.cn'
            myheaders['Referer'] = 'https://oc.sjtu.edu.cn/'
            resp_from_oauth = requests.get(resp_from_openidconnect.headers['Location'], headers=myheaders, cookies=all_cookies, allow_redirects=False)
            _debug_show_resp(resp_from_oauth, addition_msg="(3)")
            all_cookies = update_cookies(all_cookies, resp_from_oauth.cookies)
            # for cooky in resp_from_oauth.cookies:
            #     if cooky.name == 'JSESSIONID':
            #         oauth2_jsession_cookie = cookiejar_from_dict({'JSESSIONID':cooky.value})

            del myheaders['Referer']
            # for cooky in all_cookies:
            #     if cooky.name != 'jaoauth2021':
            #         all_cookies.pop(cooky.name)
            resp_from_jalogin = requests.get(resp_from_oauth.headers['Location'], headers=myheaders, cookies=all_cookies)
            _debug_show_resp(resp_from_jalogin, addition_msg="(4)")
            all_cookies = update_cookies(all_cookies, resp_from_jalogin.cookies)

            captcha_id = re_search(r'img.src = \'captcha\?(.*)\'', resp_from_jalogin.text)
            if not captcha_id:
                print('Captcha not found! Retrying...')
                continue
            captcha_id += get_timestamp()
            captcha_url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?' + captcha_id
            captcha = requests.get(captcha_url, cookies=all_cookies, headers={'Referer': 'https://jaccount.sjtu.edu.cn/jaccount', 'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Kmyhtml, like Gecko) Chrome/80.0.3987.87 Safari/537.36"})
            update_cookies(all_cookies, captcha.cookies)
            _debug_show_resp(captcha, addition_msg="(5)")

            with open('captcha.jpeg', 'wb') as f:
                f.write(captcha.content)
            code = autocaptcha('captcha.jpeg').strip()

            sid = re_search(r'sid" value="(.*?)"', resp_from_jalogin.text)
            returl = re_search(r'returl" value="(.*?)"', resp_from_jalogin.text)
            se = re_search(r'se" value="(.*?)"', resp_from_jalogin.text)
            client = re_search(r'client" value="(.*?)"', resp_from_jalogin.text)
            uuid = re_search(r'captcha\?uuid=(.*?)&t=', resp_from_jalogin.text)
            if not (sid and returl and se and uuid):
                print('Params not found! Retrying...')
                continue
            data = {'sid': sid, 'returl': returl, 'se': se, 'client': client, 'user': username,
                    'pass': password, 'captcha': code, 'g-recaptcha-response': '', 'uuid': uuid}

            """*************************** G A ******************************"""
            print("Starting GA......")
            GA_cookie = {'_gat': "1"}
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
            cookies = driver.get_cookies()
            for cookie in cookies:
                GA_cookie[str(cookie['name'])] = cookie['value']
            driver.quit()
            """*************************** G A ******************************"""
            # print(GA_cookie)
            all_cookies = update_cookies(all_cookies, cookiejar_from_dict(GA_cookie))

            site_sum = "QP6YR9D8CK"

            myheaders['Referer'] = resp_from_jalogin.request.url
            myheaders['Origin'] = "https://jaccount.sjtu.edu.cn"
            resp_from_ulogin = requests.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', headers=myheaders, data=data, cookies=all_cookies, allow_redirects=False)
            _debug_show_resp(resp_from_ulogin, addition_msg="(6)")
            cookie_of_ulogin = resp_from_ulogin.cookies
            if 'JAAuthCookie' not in dict_from_cookiejar(cookie_of_ulogin):
                continue
            all_cookies = update_cookies(all_cookies, cookie_of_ulogin)

            del myheaders['Origin']
            jump1_url = "https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location']
            resp_from_jump1 = requests.get(jump1_url, cookies=all_cookies, headers=myheaders, allow_redirects=False)
            _debug_show_resp(resp_from_jump1, addition_msg="resp_from_jump1")
            all_cookies = update_cookies(all_cookies, resp_from_jump1.cookies)

            all_cookies = update_cookies(all_cookies, cookiejar_from_dict({'_ga_QP6YR9D8CK': "GS" + GA_cookie['_gid'][2:6] + GA_cookie['_gid'][17:27] + ".1.0." + GA_cookie['_gid'][17:27] + ".0.0.0"}))
            all_cookies = update_cookies(all_cookies, resp_from_oauth.cookies)
            jump2_url = resp_from_jump1.headers['Location']
            resp_from_jump2 = requests.get(jump2_url, cookies=all_cookies, headers=myheaders, allow_redirects=False)
            _debug_show_resp(resp_from_jump2, addition_msg="resp_from_jump2")

            for cooky in all_cookies:
                if cooky.name not in ['log_session_id','pre.oc.sjtu','_csrf_token','_normandy_session','_ga','_gid','_gat','_ga_QP6YR9D8CK']:
                    all_cookies.pop(cooky.name)
            myheaders['Referer']='https://jaccount.sjtu.edu.cn/'
            myheaders['Host'] = 'oc.sjtu.edu.cn'
            jump3_url=resp_from_jump2.headers['Location']
            resp_from_jump3=requests.get(jump3_url,cookies=all_cookies,headers=myheaders,allow_redirects=False)
            _debug_show_resp(resp_from_jump3)
            all_cookies=update_cookies(all_cookies,resp_from_jump3.cookies)

            print("lalala")
            print(all_cookies)

            del myheaders['Referer']
            resp_from_oc = requests.get("https://oc.sjtu.edu.cn/?login_success=1", headers=myheaders, cookies=all_cookies)
            _debug_show_resp(resp_from_oc)
            print("lalala")
            print(resp_from_oc.text)

            return 1


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
