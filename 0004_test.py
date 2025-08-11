from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import os
import traceback
import json
import requests


'''
出租车票识别接口地址https://api.xf-yun.com/v1/private/sb6db0171；
appid、apiSecret、apiKey请到讯飞开放平台控制台获取并填写到此demo中；
图像数据，base64编码后大小不得超过4M
'''
# 请到控制台获取以下信息，并填写
APPId = "de57324f"
APISecret = "NDMzMjM2NmU3ODc1MTU5ODIzNTIwMDFi"
APIKey = "f62a350dd82ab0942b3bbc2f5a4885bc"
# 出租车图片位置
with open(r"C:\Users\13916\Desktop\wechat_2025-07-30_190907_709.png", "rb") as f:
    imageBytes = f.read()


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


# calculate sha256 and encode to base64
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


# build websocket auth request url
def assemble_ws_auth_url(requset_url, method="POST", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)


url = 'https://api.xf-yun.com/v1/private/sb6db0171'

body = {
    "header": {
        "app_id": APPId,
        "status": 3,
    },
    "parameter": {
        "sb6db0171": {
            "template_list": "taxi_ticket",
            "result": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "json"
            }
        }
    },
    "payload": {
        "sb6db0171_data_1": {
            "encoding": "jpg",
            "image": str(base64.b64encode(imageBytes), 'UTF-8'),
            "status": 3
        }
    }
}

request_url = assemble_ws_auth_url(url, "POST", APIKey, APISecret)

headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'app_id': APPId}
print(request_url)
response = requests.post(request_url, data=json.dumps(body), headers=headers)
print(response)
# print(response.content)
print("resp=>" + response.content.decode())
tempResult = json.loads(response.content.decode())
finalResult = base64.b64decode(tempResult['payload']['result']['text']).decode()
finalResult = finalResult.replace(" ", "").replace("\n", "").replace("\t", "").strip()
print("text字段Base64解码后=>" + finalResult)
