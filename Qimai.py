#!/usr/bin/python3
"""
@file:Qimai.py
@time:2019/12/10-15:33
"""
# r=f[Ja](f[Me](m, b))
# b  "00000008d78d46a"
# e -a[Gt](f[Rl])(T)
# m 的生成函数---三参+URL 后缀+e 生成 m

# 1、获取选择项列表 https://api.qimai.cn/rank/marketList?
# 2、根据主分类和子分类选择 https://api.qimai.cn/rank/marketRank?
# 3、构造参数请求列表 以及 翻页接口
import copy
import datetime
import os
import pickle
from pprint import pprint
import time

import requests
from requests.utils import dict_from_cookiejar

from .Qlogin import QiMainLogin, headers, COOKIEFILE

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
        self.market_url = "https://www.qimai.cn/rank/marketRank"
        self.marketList_api = "https://api.qimai.cn/rank/marketList"
        self.marketRank_api = "https://api.qimai.cn/rank/marketRank"
        self.headers = copy.deepcopy(headers)
        self.download_url = "https://www.qimai.cn/andapp/downTotal/appid/"
        self.download_api = "https://api.qimai.cn/andapp/downLoad"
        self.search_url = "https://www.qimai.cn/search/android/market/9/search/"
        self.search_api = "https://api.qimai.cn/search/android"

    def read_cookies(self):
        if os.path.exists(COOKIEFILE):
            with open(COOKIEFILE, "rb") as f:
                # 将字典转换成RequestsCookieJar，赋值给session的cookies.
                cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            return cookies
        else:
            return None

    def request_marketList(self):
        # 首先获取analysis的值
        analysis = self.lxb.get_my_analysis(
            self.market_url, self.marketList_api)
        params = {
            "analysis": analysis
        }
        # print("3:", dict_from_cookiejar(self.session.cookies))
        resp = self.session.get(self.marketList_api,
                                params=params, headers=self.headers)
        pprint(resp.json())  # 看数字的意义 取消注释

    def request_search(self, channel, name):
        params = {
            "search": name,
            "page": '1',
            "market": CHANNEL_ID[channel]
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis(
            self.search_url + name, self.search_api, params_list)
        params['analysis'] = analysis
        resp = self.session.get(
            self.search_api, params=params, headers=self.headers)
        appId = 0
        try:
            print(resp.json()['appList'][0]['appInfo'], name)
            if name in resp.json()['appList'][0]['appInfo']['appName']:
                appId = resp.json()['appList'][0]['appInfo']['appId']  # 匹配名字
        except Exception as e:
            print(e)
        return appId

    def request_search_appInfo(self, channel, name):
        params = {
            "search": name,
            "page": '1',
            "market": CHANNEL_ID[channel]
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis(
            self.search_url + name, self.search_api, params_list)
        params['analysis'] = analysis
        resp = self.session.get(
            self.search_api, params=params, headers=self.headers)
        respJson = resp.json()
        appInfo = None
        # print(resp.json()['appList'])
        if 'appList' in respJson:
            appList = respJson["appList"]
            # 完全匹配
            for app in appList:
                if name == app['appInfo']['appName']:
                    appInfo = app['appInfo']
                    return appInfo
            # 包含
            if appInfo == None:
                for app in appList:
                    dimName = [name + '（', name + '(', name + ' (']
                    for dim in dimName:
                        if dim in app['appInfo']['appName'] and app['appInfo']['appName'].index(dim) == 0:
                            appInfo = app['appInfo']
                            return appInfo
        else:
            print("error", respJson)
        return appInfo

    def request_download(self, channel, appId, sdate, edate):
        params = {
            "appid": appId,
            "type": "day",
            "sdate": sdate,  # "2019-08-26"
            "edate": edate  # "2019-09-01"
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis(
            self.download_url + appId, self.download_api, params_list)
        params['analysis'] = analysis
        # self.headers["User-Agent"] = UserAgent(verify_ssl=False).random
        resp = self.session.get(
            self.download_api, params=params, headers=self.headers)
        download = {}
        # OPPO VIVO 华为
        try:
            dataList = resp.json()['data']
            for data in dataList:
                if data['name'] == channel:
                    for d in data['data']:
                        download[str((int)(d[0] / 1000))] = d[1]
        except Exception as e:
            print(e)
        return download

    def request_marketRank(self):
        # 若登录失败则退出
        if self.loginError:
            return
        # 6代表华为 14代表商务 看全部见request_marketList
        market_id = input("输入大分类数字如6>>")
        category_id = input("输入子分类数字如14>>")
        # date = input("输入日期>>")
        #             "analysis": analysis,
        #             # "collection": "topselling_free",
        #             # "country": "cn",
        params = {
            "market": market_id,
            "category": category_id,
            "date": datetime.date.today().strftime('%Y-%m-%d')
        }

        page = 1
        maxPage = 0

        while True:
            if page != 1:
                params['country'] = 'cn'
                params['collection'] = 'topselling_free'
                params.pop('analysis')
            params_list = list(params.values())

            analysis = self.lxb.get_my_analysis(
                self.market_url, self.marketRank_api, params=params_list)
            params['analysis'] = analysis
            resp = self.session.get(
                self.marketRank_api, params=params, headers=self.headers)
            results = resp.json()
            if maxPage == 0:
                maxPage = int(results.get("maxPage"))
                print("maxPage:", maxPage)

            if results.get("code") == 10000:
                rankInfos = results.get("rankInfo")
                for rankInfo in rankInfos:
                    item = dict()
                    item['appName'] = rankInfo.get('appInfo').get('appName')
                    item['publisher'] = rankInfo.get(
                        'appInfo').get('publisher')
                    item['app_comment_score'] = rankInfo.get(
                        'appInfo').get('app_comment_score')
                    item['app_comment_count'] = rankInfo.get(
                        'appInfo').get('app_comment_count')
                    print(item)
            else:
                print("error in rank:", results)

            page = page + 1
            if page > maxPage:
                print("exit")
                break
            else:
                print("continue")
                params['page'] = str(page)

    def request_rank(self):
        params = {
            "brand": "all",
            "genre": "6014",
            "device": "iphone",
            "country": "us",
            "date": "2019-10-16",
            "page": "1"
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis("https://www.qimai.cn/rank/index/brand/all/genre/6014/device/iphone/country/us",
                                            "https://api.qimai.cn/rank/indexPlus/brand_id/0", params=params_list)
        params['analysis'] = analysis
        print(params)
        resp = self.session.get(
            "https://api.qimai.cn/rank/indexPlus/brand_id/0", params=params, headers=self.headers)
        results = resp.json()
        print(results)

    def request_freeRank(self, country, sdate, page):
        params = {
            "brand": "free",
            "genre": "6014",
            "device": "iphone",
            "country": country,  # us cn
            "date": sdate,  # 2019-10-17
            "page": page,  # 1 2 一次50条
            "is_rank_index": "1"
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis(
            "https://www.qimai.cn/rank/index/brand/free/country/us/genre/6014/device/iphone", "https://api.qimai.cn/rank/index", params=params_list)
        params['analysis'] = analysis
        resp = self.session.get(
            "https://api.qimai.cn/rank/index", params=params, headers=self.headers)
        results = resp.json()
        if 10000 == results["code"]:
            return results["rankInfo"]
        else:
            return None

    def request_rankMore(self, appId, country, sdate, edate):
        params = {
            "appid": appId,  # 1460358976
            "country": country,  # cn
            "brand": "free",
            "subclass": "all",
            "sdate": sdate,  # 2018-10-16
            "edate": edate  # 2019-10-16
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis("https://www.qimai.cn/app/rank/appid/" + appId +
                                            "/country/" + country, "https://api.qimai.cn/app/rankMore", params=params_list)
        params['analysis'] = analysis
        resp = self.session.get(
            "https://api.qimai.cn/app/rankMore", params=params, headers=self.headers)
        results = resp.json()
        if 10000 == results["code"]:
            return results["data"]
        else:
            return None

    def request_appInfo(self, appId, country):
        params = {
            "appId": appId,
            "country": country
        }
        params_list = list(params.values())
        # https://www.qimai.cn/app/baseinfo/appid/" + appId + "/country/"
        analysis = self.lxb.get_my_analysis("https://www.qimai.cn/app/baseinfo/appid/" + appId +
                                            "/country/" + country, "https://api.qimai.cn/app/baseinfo", params=params_list)
        params['analysis'] = analysis
        print(params)
        resp = self.session.get(
            "https://api.qimai.cn/app/baseinfo", params=params, headers=self.headers)
        results = resp.json()
        print(results)

    '''
    根据应用ID、国家，获取关键词列表
    '''

    def request_keywords(self, appId, country):
        params = {
            "appid": appId,  # 1460358976
            "country": country,  # cn
            "version": "ios12"
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis("https://www.qimai.cn/app/keyword/appid/" + appId +
                                            "/country/" + country, "https://api.qimai.cn/app/keyword", params=params_list)
        params['analysis'] = analysis
        resp = self.session.get(
            "https://api.qimai.cn/app/keyword", params=params, headers=self.headers)
        results = resp.json()
        if 10000 == results["code"]:
            return results["keywordList"]
        else:
            return None

    '''
    根据关键词、国家、开始日期、结束日期，获取关键词热度
    '''

    def request_keywordMore(self, keyword, country, sdate, edate):
        params = {
            "word[0]": keyword,
            "device": "iphone",
            "country": country,
            "sdate": sdate,
            "edate": edate
        }
        analysis = self.lxb.get_my_analysis(
            "https://www.qimai.cn/app/searchHints/device/iphone/word", "https://api.qimai.cn/app/searchHints")
        resp = self.session.post(
            "https://api.qimai.cn/app/searchHints?analysis=" + analysis, data=params, headers=self.headers)
        results = resp.json()
        if 10000 == results["code"]:
            return results["data"]
        else:
            return None

    '''
    根据日期、页数、国家，获取关键词榜单信息
    '''

    def request_keywordRank(self, dateStr, page, country="cn"):
        params = {
            "is_inc": "0",
            "date": dateStr,
            "country": country,
            "page": page,
            "genre": "6014"
        }
        analysis = self.lxb.get_my_analysis("https://www.qimai.cn/trend/keywordRank/is_inc/0/date/" +
                                            dateStr + "/device/iphone/country/cn/genre/6014", "https://api.qimai.cn/trend/keywordRank")
        resp = self.session.post(
            "https://api.qimai.cn/trend/keywordRank?analysis=" + analysis, data=params, headers=self.headers)
        results = resp.json()
        # print(results)
        if 10000 == results["code"]:
            return results["wordRankList"]
        else:
            return None

    '''
    根据发行商ID、国家，获取所有应用信息
    '''

    def request_appInfosByPublishId(self, publishId, country):
        params = {
            "id": publishId,
            "country": country,  # us cn
            "kind": "softwareDeveloper"
        }
        params_list = list(params.values())
        analysis = self.lxb.get_my_analysis("https://www.qimai.cn/detail/publisher/id/" + publishId +
                                            "/country/us", "https://api.qimai.cn/search/searchExtendDetail", params=params_list)
        params['analysis'] = analysis
        resp = self.session.get(
            "https://api.qimai.cn/search/searchExtendDetail", params=params, headers=self.headers)
        results = resp.json()
        if 10000 == results["code"]:
            return results["data"]
        else:
            return None


if __name__ == '__main__':
    qimai = QimaiApi()
    qimai.request_appInfo("1287282214", "us")
