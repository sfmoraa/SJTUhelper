from time import sleep
from time import time
from getpass import getpass
import pytesseract
from PIL import Image, ImageEnhance

import re
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict
from tenacity import retry, retry_if_exception_type, wait_fixed


class AutomataError(Exception):
    """
    Base exception class.
    """


class RetryRequest(RequestException):
    """
    retry request function.
    """


class CustomAdapter(HTTPAdapter):
    def build_response(self, req, resp):
        # 解析Set-Cookie头部中的Cookie字符串
        if 'Set-Cookie' in resp.headers:
            cookies = {}
            set_cookie_headers = resp.headers.get_all('Set-Cookie')
            for header in set_cookie_headers:
                cookie_parts = header.split(';')
                cookie = cookie_parts[0].strip()
                cookie_name, cookie_value = cookie.split('=')
                cookies[cookie_name] = cookie_value

            # 将解析后的Cookie添加到会话的cookies属性中
            former_cookie = dict_from_cookiejar(req._cookies)
            for item in cookies:
                former_cookie[str(item)] = cookies[str(item)]
            cookiejar = cookiejar_from_dict(former_cookie)
            req._cookies = cookiejar

            # 打印请求的详细信息
            print("URL:", req.url)
            print("Method:", req.method)
            print("Headers:", req.headers)
            print("Body:", req.body)
            print("Cookies:", req.headers.get('Cookie'))
            print("resp:",resp.headers)
            print("---------------------------------")


        return super().build_response(req, resp)


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


def _create_session():
    session = requests.Session()
    print("session", session)
    # session.mount('http://', HTTPAdapter(max_retries=3))
    # session.mount('https://', HTTPAdapter(max_retries=3))
    session.mount('http://', CustomAdapter())
    session.mount('https://', CustomAdapter())
    # session.verify = False    # WARNING! Only use it in Debug mode!
    return session


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _get_login_page(session, url):
    # return page text
    req = session.get(url)
    # if last login exists, it will go to error page. so ignore it
    if '<form id="form-input" method="post" action="ulogin">' in req.text:
        return req.text
    else:
        raise RetryRequest  # make it retry


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _bypass_captcha(session, url, useocr):
    # return captcha code
    # cookie_dict = dict_from_cookiejar(session.cookies)
    captcha = session.get(url, headers={'Referer': 'https://jaccount.sjtu.edu.cn/jaccount', "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36" })# ,'Cookie': '; '.join([f'{k}={v}' for k, v in cookie_dict.items()])})
    print("captcha:", captcha, url)
    with open('captcha.jpeg', 'wb') as f:
        f.write(captcha.content)

    if useocr:
        code = autocaptcha('captcha.jpeg').strip()
        if not code.isalpha():
            code = '1234'  # cant recongnize, go for next round
    else:
        img = Image.open('captcha.jpeg')
        img.show()
        code = input('Input the code(captcha.jpeg): ')

    return code


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _login(session, sid, returl, se, client, username, password, code, uuid):
    # return 0 suc, 1 wrong credential, 2 code error, 3 30s ban
    data = {'sid': sid, 'returl': returl, 'se': se, 'client': client, 'user': username,
            'pass': password, 'captcha': code, 'v': '', 'uuid': uuid}
    session.cookies.update(session.cookies)
    req = session.post(
        'https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data,cookies=session.cookies)

    # result
    # be careful return english version website in english OS
    if '请正确填写验证码' in req.text or 'wrong captcha' in req.text:
        return 2
    elif '请正确填写你的用户名和密码' in req.text or 'wrong username or password' in req.text:
        return 1
    elif '30秒后' in req.text:  # 30s ban
        return 3
    elif '<i class="fa fa-gear" aria-hidden="true" id="wdyy_szbtn">':
        # print(":::",req.text)
        return 0
    else:
        raise AutomataError


def print_url(r, *args, **kwargs):
    print("--------url here:",r.url)
    print("Status Code:", r.status_code)
    print("Headers:", r.headers)
    print("Cookies:", r.cookies)
    # print("Content:", r.text)
    print("--------")


def login(url, useocr=True):
    """Call this function to login.

    Captcha picture will be stored in captcha.jpeg.
    WARNING: From 0.2.0, username and password will not be allowed to pass as params, all done by this function itself.

    Args:
        url: string, direct login url
        useocr=False: bool, True to use ocr to autofill captcha

    Returns:
        requests login session.
    """
    while True:
        # username = input('Username: ')
        username=                                                                                                                                                                       'sfx-sjtu'
        print(1)
        # password = input('Password(no echo): ')
        password=                                                                                                                                                                                                           'fly618753294FLY'
        print(2)
        while True:
            session = _create_session()

            print("!!!!!!!!debug place 1")
            for cookie in session.cookies:
                print(cookie.name, "=", cookie.value)
            print("!!!!!!!!debug place 1 over")

            session.hooks['response'].append(print_url)
            req = _get_login_page(session, url)

            print("!!!!!!!!debug place 2")
            for cookie in session.cookies:
                print(cookie.name, "=", cookie.value)
            print("!!!!!!!!debug place 2 over")

            captcha_id = re_search(r'img.src = \'captcha\?(.*)\'', req)
            if not captcha_id:
                print('Captcha not found! Retrying...')
                sleep(3)
                continue
            captcha_id += get_timestamp()
            captcha_url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?' + captcha_id
            code = _bypass_captcha(session, captcha_url, useocr)

            print("!!!!!!!!debug place 3")
            for cookie in session.cookies:
                print(cookie.name, "=", cookie.value)
            print("!!!!!!!!debug place 3 over")

            sid = re_search(r'sid" value="(.*?)"', req)
            returl = re_search(r'returl" value="(.*?)"', req)
            se = re_search(r'se" value="(.*?)"', req)
            client = re_search(r'client" value="(.*?)"', req)
            uuid = re_search(r'captcha\?uuid=(.*?)&t=', req)
            if not (sid and returl and se and uuid):
                print('Params not found! Retrying...')
                sleep(3)
                continue

            res = _login(session, sid, returl, se, client,
                         username, password, code, uuid)

            print("!!!!!!!!debug place 4")
            for cookie in session.cookies:
                print(cookie.name, "=", cookie.value)
            print("!!!!!!!!debug place 4 over")

            if res == 2:
                if not useocr:
                    print('Wrong captcha! Try again!')
                continue
            elif res == 1:
                print('Wrong username or password! Try again!')
                break
            elif res == 3:
                print('Opps! You are banned for 30s...Waiting...')
                sleep(30)
                continue
            else:
                return session
