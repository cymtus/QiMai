"""
@file:Qlogin.py
@time:2019/8/2-14:26
"""
# 七麦数据模拟登录
import copy
import pickle
import time
from urllib.request import urlretrieve

import execjs
from urllib.parse import urlparse, urlencode
import requests
from PIL import Image
from requests.utils import dict_from_cookiejar

with open('Qimai.js', encoding='utf-8') as f:
    jsdata = f.read()
ctx = execjs.compile(jsdata)
COOKIEFILE = "qimai.txt"
b = "00000008d78d46a"
headers = {
    "Accept": "application/json, text/plain, */*",
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://www.qimai.cn',
    "Referer": "https://www.qimai.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/59.0"
}


def get_cookie_synct_e(cookies):
    # 首先访问时只有synct而没有syncd,可推断syncd是用Js写入的而不是后台设置。
    # cookies = response.cookies.get_dict()
    if "syncd" in cookies.keys():
        pass
    else:
        synct = cookies.get('synct')
        #     var g = new Date() - 1000 * synct;
        #     var e = new Date() - g - 1515125653845;
        e = 1000 * float(synct) - 1515125653845
        return e


def generate_m(e, url, params=None):
    path = urlparse(url).path
    H, S, nua, ndo = "@#", '1', path, "https://api.qimai.cn"
    if not params:
        # "@#/account/pageCheck/type/signin@#49805788240@#1"
        m = []
    else:
        # "142019-08-036"
        m = params
    m.sort()
    m = ''.join(m)
    mjs = 'v("{0}")'.format(m)
    # "MTQyMDE5LTA4LTAzNg==
    m = ctx.eval(mjs)
    m = m + H + nua.replace(ndo, "") + H + str(int(e)) + H + S
    return m


# login:eEcbVwJTX0VeRB9AWQNSewxRVQofRElAVR9DUQNZUQp0FVUJCAAGAgYFDVUHeEcF
def get_analysis(m_str, b_str):
    # v(k(m_str, b_str))
    analysis = ctx.call("get_analysis", m_str, b_str)
    return analysis


class QiMainLogin:
    def __init__(self):
        self.headers = copy.deepcopy(headers)
        self.session = requests.session()

        self.login_url = "https://www.qimai.cn/account/signin"

        self.image_api = 'https://api.qimai.cn/account/getVerifyCodeImage?{}'.format(
            str(int(time.time() * 1000)))
        self.login_api = "https://api.qimai.cn/account/signinForm?"
        self.user_api = "https://api.qimai.cn/account/userinfo"

    def get_verifyCode(self):
        # 直接将远程数据下载到本地
        urlretrieve(self.image_api, 'captcha.png')
        captcha = Image.open('captcha.png')
        captcha.show()

        verify_code = input('请输入验证码>> ')

        return verify_code

    def login_qimai(self):
        analysis = self.get_my_analysis(self.login_url, self.login_api)
        # 构造请求连接
        params = {
            'analysis': analysis
        }
        # eEcbVwJTX0VeRB9DUQNZUQpyWRNdcBMECQgHCVQACFIDByETAQ%3D%3D
        login_url_ = self.login_api + urlencode(params)
        print("login:", login_url_)
        data = {
            'username': "17521236179",  # 输入自己的账号
            'password': "zzz2b2b...",  # 输入自己的密码
            'code': self.get_verifyCode()
        }
        resp = self.session.post(login_url_, data=data, headers=self.headers)
        #
        if resp.json()['code'] == 10000:
            print('登录成功!用户名为:' + resp.json().get('userinfo').get('username'))
            # print('登录后响应Cookie:' + resp.headers.get('Set-Cookie'))
            # print(self.session.cookies) cookiejar
            # 常规套路是写入文本再读取
            with open(COOKIEFILE, 'wb') as f:
                # 将cookiejar转换成字典
                pickle.dump(requests.utils.dict_from_cookiejar(
                    self.session.cookies), f)

            return self.session.cookies
        else:
            print("login error:", resp.json())

    def get_my_analysis(self, e_url, url, params=None):
        # 生成e
        response = self.session.get(e_url, headers=self.headers)
        cookies = response.cookies.get_dict()

        # print("1:", cookies)
        if not cookies:
            cookies = dict_from_cookiejar(self.session.cookies)
            print("2:", cookies)

        e = get_cookie_synct_e(cookies)
        # 添加
        m = generate_m(e, url, params=params)
        # print("m:", m)
        analysis = get_analysis(m, b)

        return analysis

    def check_login(self, cookies):
        """
        检测Cookies是否失效
        :param cookies:
        :return:
        """
        info_url = "https://www.qimai.cn"
        analysis = self.get_my_analysis(info_url, self.user_api)

        params = {
            'analysis': analysis
        }
        resp = requests.get(self.user_api, params=params,
                            cookies=cookies, headers=self.headers)
        resp_dict = resp.json()
        username = resp_dict.get("userinfo").get("username")
        if username == "":
            print("invalid")
            return None
        else:
            print("valid")
            return 1


# m = "MTQyMDE5LTA4LTAzNg==@#/rank/marketRank@#49871507911@#1"

if __name__ == '__main__':
    lxb = QiMainLogin()
    cookiesjar = lxb.login_qimai()
    # cookies = dict_from_cookiejar(cookiesjar)
    # lxb.check_login(cookiesjar)
