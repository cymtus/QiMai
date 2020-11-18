#!/usr/bin/python3
"""
@file:Qimai.py
@time:2019/8/1-9:21
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

import pymongo
import requests
from requests.utils import dict_from_cookiejar

from Qlogin import QiMainLogin, headers, COOKIEFILE

import random
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

CHANNEL_ID = {
    "OPPO": "9",
    "VIVO": "8",
    "华为": "6"
}


class DataList:
    def __init__(self):
        cookies_in_file = self.read_cookies()
        client = pymongo.MongoClient(
            host='192.168.1.171', port=27017)  # tomatonet.asuscomm.com

        self.lxb = QiMainLogin()
        self.appLogCollection = client.TomatoMarket.AppLog
        self.rankCollection = client.TomatoMarket.Rank
        self.oppoRankCollection = client.TomatoMarket.OPPORank
        self.vivoRankCollection = client.TomatoMarket.VIVORank
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
                    # print(name, appInfo)
                    return appInfo
            # 包含
            if appInfo == None:
                for app in appList:
                    dimName = [name + '（', name + '(', name + ' (']
                    for dim in dimName:
                        if dim in app['appInfo']['appName'] and app['appInfo']['appName'].index(dim) == 0:
                            appInfo = app['appInfo']
                            # print(name, appInfo)
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

    # https://api.qimai.cn/rank/marketRank?analysis=dTBlTyx0dQV8ZHEEdDB2CCpZeBRUdwlHUwJmSwZwVBFuB1hdU11mXHATFxZWVg8bWwBCW1VEYlFeUyQUDF0MD1MDAwkABgNwG1U%3D&market=6&category=14&country=cn&collection=topselling_free&date=2019-08-04
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

    def crawlerAppInfo(self, channel, stime, etime):
        print("========开始抓取 " + channel + ", " + self.getTimeStr(self.getLastZoneTime()) + "=============")
        rankss = self.rankCollection.find({"time":{"$gte":stime, "$lte":etime}, "channel":channel})
        sdata = time.strftime("%Y-%m-%d", time.localtime(stime))
        edate = time.strftime("%Y-%m-%d", time.localtime(etime))
        appLogs = self.appLogCollection.find({"time":{"$gte":stime, "$lte":etime}, "channel":channel})
        oldapps = []
        for app in appLogs:
            if not app["name"] in oldapps:
                oldapps.append(app["name"])
        print(sdata, edate)
        apps = []
        for ranks in rankss:
            for cg1 in ranks["category"]:
                for cg2 in ranks["category"][cg1]:
                    for name in ranks["category"][cg1][cg2]:
                        if not name in apps and not name in oldapps:
                            apps.append(name)
        self.update_items("thread1", channel, sdata, edate, apps)
        print("========抓取完成 " + channel + ", " + self.getTimeStr(self.getLastZoneTime()) + "=============")

    def update_items(self, threadname, channel, sdata, edate, names):
        count = 0
        for name in names:
            time.sleep(1)
            self.update_item_mongodb(channel, name, sdata, edate)
            count += 1
            print( threadname + " : " + str(count) + "/" + str(len(names)))
    
    def update_item_mongodb(self, channel, name, sdata, edate):
        appInfo = self.request_search_appInfo(channel, name)
        time.sleep(random.uniform(0.3, 1.5))
        items = []
        if appInfo != None:
            download = self.request_download(channel, appInfo["appId"], sdata, edate)
            time.sleep(random.uniform(0.3, 1.5))
            for key in download:
                item = {}
                item["channel"] = channel
                item["name"] = name
                item["qmId"] = appInfo["appId"]
                item["icon"] = appInfo["icon"]
                item["appName"] = appInfo["appName"]
                item["publisher"] = appInfo["publisher"]
                item["comment_score"] = appInfo["comment_score"]
                item["comment_count"] = appInfo["comment_count"]
                item["download"] = download[key]
                item["version_time"] = appInfo["version_time"]
                item["time"] = int(key)
                items.append(item)
            if len(items) > 0:
                self.appLogCollection.insert_many(items)

    def crawlerApps(self, channel, apps, sdate, edate):
        for app in apps:
            self.update_item_mongodb(channel, app, sdate, edate)

    def getZoneTime(self):
        today = datetime.date.today()
        today_time = int(time.mktime(today.timetuple()))
        return today_time

    def getLastZoneTime(self):
        return self.getZoneTime() - 24 * 3600

    def getTimeStr(self, stime):
        return time.strftime("%Y-%m-%d", time.localtime(stime))

    def checkCrawler(self, channel, time):
        rank = self.rankCollection.find_one({"time":time, "channel":channel})
        if None != rank:
            return True
        else:
            return False
    
    def uploadChannelRank(self, channel, stime):
        rank = self.rankCollection.find_one({"time":stime, "channel":channel})
        oldrank = self.rankCollection.find_one({"time":stime - 24 * 3600, "channel":channel})
        flag = False
        if oldrank != None:
            flag = True
        apps = self.appLogCollection.find({"channel":channel, "time":stime})
        appInfos = {}
        for app in apps:
            appInfos[app["name"]] = app["download"]
        for cg1 in rank["category"]:
            for cg2 in rank["category"][cg1]:
                cg2arr = []
                for i, name in enumerate(rank["category"][cg1][cg2]):
                    download = 0
                    if name in appInfos:
                        download = appInfos[name]
                    item = {"name":name, "download":download}
                    pos = 0
                    if flag:
                        try:
                            pos = oldrank["category"][cg1][cg2].index(name) - i
                            pos *= 2
                        except Exception as e:
                            pos = -1
                        item["pos"] = pos
                    cg2arr.append(item)
                rank["category"][cg1][cg2] = cg2arr
        rank.pop("_id")
        if "OPPO" == channel:
            oppoRank = self.oppoRankCollection.find_one({"time":stime, "channel":channel})
            if None == oppoRank:
                self.oppoRankCollection.insert_one(rank)
            else:
                self.oppoRankCollection.replace_one({"_id": oppoRank["_id"]}, rank)
        elif "VIVO" == channel:
            vivoRank = self.vivoRankCollection.find_one({"time":stime, "channel":channel})
            if None == vivoRank:
                self.vivoRankCollection.insert_one(rank)
            else:
                self.vivoRankCollection.replace_one({"_id": oppoRank["_id"]}, rank)


def func():
    print("抓取数据")
    market = DataList()
    # market.crawlerAppInfo("OPPO", 1574006400, 1575302400)
    # time.sleep(10)
    market.crawlerAppInfo("VIVO", 1574006400, 1575302400)
    # stime = market.getLastZoneTime()
    # if market.checkCrawler("OPPO", stime):
    #     market.crawlerAppInfo("OPPO", stime, stime)
    #     time.sleep(1)
    #     market.uploadChannelRank("OPPO", stime)
    # time.sleep(5)
    # if market.checkCrawler("VIVO", stime):
    #     market.crawlerAppInfo("VIVO", stime, stime)
    #     time.sleep(1)
    #     market.uploadChannelRank("VIVO", stime)

if __name__ == '__main__':
    func()
    # scheduler = BlockingScheduler()
    # scheduler.add_job(func, 'cron', day_of_week='0-6',
                    #   hour=11, minute=30)
    # scheduler.start()