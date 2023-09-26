import requests
import openai
import pandas as pd
import re
from lxml import etree
from time import time, localtime, strftime
from PIL import Image, ImageEnhance
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
    for repository in sections:
        author = repository.xpath("./h2/a/span//text()")[0].strip()[:-2]
        title = repository.xpath("./h2/a/text()")[-1].strip()
        if len(repository.xpath("./p/text()")):
            description = repository.xpath("./p/text()")[0].strip()
        else:
            description = "/"
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


def process_captcha_and_GA(resp, session, username, password, return_driver=False):
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

    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'], path=cookie['path'])
    session.cookies.set('_gat', "1")
    if return_driver:
        return session, data, driver
    else:
        driver.quit()
        return session, data
    """*************************** G A ******************************"""


def dekt():
    username = input('Username: ')
    password = input('Password: ')
    dekt_login_url = 'https://jaccount.sjtu.edu.cn/oauth2/authorize?response_type=code&client_id=sowyD3hGhP6f6O92bevg&redirect_uri=https://dekt.sjtu.edu.cn/h5/index&state=&scope=basic'
    myheaders = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    dekt_session = requests.Session()
    resp_from_oauth_start = dekt_session.get(dekt_login_url, headers=myheaders)
    dekt_session, data, mydriver = process_captcha_and_GA(resp_from_oauth_start, dekt_session, username, password, True)
    resp = dekt_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data)
    print("rrrrrrrrrrrrrrrrrrrrrr")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://dekt.sjtu.edu.cn/")

    for cookie in dekt_session.cookies:
        print(cookie.name, cookie.value, cookie.path, cookie.domain)
        print({'name': cookie.name, 'value': cookie.value, 'path': cookie.path})
        driver.add_cookie({'name': cookie.name, 'value': cookie.value, 'path': cookie.path, 'domain': cookie.domain})
    driver.get("https://dekt.sjtu.edu.cn/h5/index")

    print(driver.current_url)
    print(driver.page_source)
    script = """
    function executeScript(url) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    resolve(xhr.responseText);
                } else {
                    reject('Request failed. Status: ' + xhr.status);
                }
            };
            xhr.onerror = function() {
                reject('Request failed. Network error.');
            };
            xhr.send();
        });
    }

    return executeScript('https://dekt.sjtu.edu.cn/h5/index/h5/static/js/app.ae584f2c.js');
    """
    '''
        return executeScript('https://dekt.sjtu.edu.cn/h5/index/h5/static/js/chunk-vendors.f37c3f31.js');

    '''
    response = driver.execute_script(script)
    print(response)

    driver.quit()
    return 111

    myhtml = etree.HTML(resp.text)
    sections = myhtml.xpath('//link[contains(@href, "static/js/Activities")]')
    href_values = [link.get("href") for link in sections]
    print(href_values)
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
    _debug_show_resp(resp_from_oauth)
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
    print(resp_from_oc.text)


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
    oauth_session = requests.Session()
    myheaders_for_oauth = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36", 'Host': "jaccount.sjtu.edu.cn"}
    while True:
        try:
            resp_from_oauth = oauth_session.get(resp_from_auth_jaccount.headers['Location'], headers=myheaders_for_oauth)
            oauth_session, data = process_captcha_and_GA(resp_from_oauth, oauth_session, username, password)
            resp_from_ulogin = oauth_session.post('https://jaccount.sjtu.edu.cn/jaccount/ulogin', headers=myheaders_for_oauth, data=data, allow_redirects=False)
            resp_from_jalogin = oauth_session.get("https://jaccount.sjtu.edu.cn" + resp_from_ulogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            resp_from_oauth2_authorize = oauth_session.get(resp_from_jalogin.headers['Location'], headers=myheaders_for_oauth, allow_redirects=False)
            break
        except Exception:
            print("oops!retrying...")
            continue
    shuiyuan_session.cookies.update(oauth_session.cookies)
    resp_from_shuiyuan = shuiyuan_session.get(resp_from_oauth2_authorize.headers['Location'], headers=myheaders_for_shuiyuan)
    resp_from_latest = shuiyuan_session.get("https://shuiyuan.sjtu.edu.cn/latest.json?ascending=false", headers=default_headers)
    infos = resp_from_latest.json()['topic_list']['topics']
    rst = []
    for index, item in enumerate(infos):
        ref = "https://shuiyuan.sjtu.edu.cn/t/topic/" + str(item['id'])
        if 'last_read_post_number' in item:
            ref += '/' + str(item['last_read_post_number'])
        rst.append([ref, item['title'], item['posts_count'], item['reply_count'], item['unseen'], shuiyuan_category_dict[str(item['category_id'])], item['tags'], item['views']])
    pd.DataFrame(columns=['ref', 'title', 'posts_count', 'reply_count', 'unseen', 'category', 'tags', 'views'], data=rst).to_csv('PERSONAL_shuiyuanLatest.csv', encoding='utf-8')
    # 仅当种类字典需要更新时才调用此函数
    # update_shuiyuan_category(shuiyuan_session,default_headers)

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
    rst = []
    for event in calendar_list.json()['data']['events']:
        rst.append([event["title"], event["startTime"], event["endTime"], event["location"], "https://calendar.sjtu.edu.cn/api/event/detail?id=" + event['eventId']])
    rst = sorted(rst, key=lambda x: x[1])
    pd.DataFrame(columns=['title', 'startTime', 'endTime', 'location', 'json_detail_url'], data=rst).to_csv('PERSONAL_calendar.csv', encoding='utf-8')


zhihu_cookie = '_zap=7c19e78f-cc24-40ba-b901-03c5dbc6f5c6; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1695046455; d_c0=AqCUdcs8ahePTm1AlskR2GlKJRZsIi6BHoU=|1695046467; captcha_session_v2=2|1:0|10:1695046472|18:captcha_session_v2|88:U09XVkptekkzbFRRV1hVT1d3ZTZBbmtpNUpndFBYSjBiZ2QxYStSTmZMV001ejY4VU1NK2xTQ3c0WFRTUG4wSQ==|6e425e767457afc3f0c45ccddcaa97fb6e33acf05881980271a533dcc949768e; __snaker__id=9sk6FFpO9I1GGW59; gdxidpyhxdE=LP%2FMjewee%5CMfdkd9rynOLe5BzZBXLU2sK7h%5Cw5TVTm81fomi%2FfUw8vt3baTUeLiszRTP4Irv9PIP%2F%5CNlk533r%2BqSyPpuzMqYdMleidTIalNRae3q5cU6SnNBDIr5tW%5CmtQ4KgZ0OoU1Yn4%5CBE%5C4VrV3RzWjeRLpPEGsRjNv%5C2zoQNRhP%3A1695047380796; z_c0=2|1:0|10:1695046490|4:z_c0|92:Mi4xYVJJZ0RnQUFBQUFDb0pSMXl6eHFGeVlBQUFCZ0FsVk5XcW4xWlFBUkJSRmZ4V3JnWEEzMVlWeWlQQkRHS1JLNzVn|dc53aefcc4aca1ea26078128ae2bbd47513c720ee18127cd27ab30c94d9815db; q_c1=f57083c332484af5a73c717d3f3a0401|1695046490000|1695046490000; tst=h; _xsrf=c3051616-3649-4d34-a21a-322dcdcc7b34; KLBRSID=c450def82e5863a200934bb67541d696|1695261410|1695261410'
if __name__ == '__main__':
    # get_github_trending()
    # get_zhihu_hot_topic(zhihu_cookie)
    # get_bilibili_ranking()
    # get_gold_price()
    # print(gpt_filter('zhihu'))
    # get_weibo_hot_topic()
    # dekt()
    # canvas()
    # shuiyuan()
    # mysjtu_calendar()
    print("over")
