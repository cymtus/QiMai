import copy
import os
import pickle
from flask import Flask
import requests

from Qlogin import COOKIEFILE, QiMainLogin, headers

app = Flask(__name__)

CHANNEL_ID = {
    "360": "1",
    "百度": "2",
    "应用宝": "3",
    "小米": "4",
    "豌豆荚": "5",
    "华为": "6",
    "魅族": "7",
    "VIVO": "8",
    "OPPO": "9"
}


class QimaiApi:
    def __init__(self):
        cookies_in_file = self.read_cookies()
        self.lxb = QiMainLogin()
        # 先从文件读取cookie判断是否有效,若无效则登录
        self.session = requests.session()

        self.loginError = 0
        if cookies_in_file and self.lxb.check_login(cookies_in_file):
            self.session.cookies = cookies_in_file
        else:
            print("Now ReLogin")
            cookiesjar = self.lxb.login_qimai()
            if cookiesjar is None:
                print("登录失败,请检查用户名密码")
                self.loginError = 1
            else:
                self.session.cookies = cookiesjar
        # GET
        self.headers = copy.deepcopy(headers)
        self.check_publisher_url = "https://www.qimai.cn/detail/publisher/id/"
        self.check_publisher_api = "https://api.qimai.cn/search/searchExtendDetail"

    def read_cookies(self):
        if os.path.exists(COOKIEFILE):
            with open(COOKIEFILE, "rb") as f:
                # 将字典转换成RequestsCookieJar，赋值给session的cookies.
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            return cookies
        else:
            return None

    def check_publisher(self, publisherId, device, country):
        params = {
            'id': publisherId,
            'kind': 'softwareDeveloper',
            'device': device,
            'country': country
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis(
            self.check_publisher_url + publisherId + "/device" + device + "/country" + country,
            self.check_publisher_api, params_list)
        params['analysis'] = analysis
        print(params)
        resp = self.session.get(
            self.check_publisher_api, params=params, headers=self.headers)
        if 10000 == resp.json()["code"]:
            return resp.json()["data"]
        else:
            return None


# 根据厂商ID判断是否存在厂商 并且返回厂商信息
@app.route('/getPublisher/<publisherId>/<device>/<country>')
def getPublisher(publisherId, device, country):
    api = QimaiApi()
    return api.getPublisher(publisherId, device, country)


if __name__ == '__main__':
    app.run()
