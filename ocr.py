import base64
from hashlib import md5
import os
import time
import uuid
import requests
import re
import ujson
from concurrent.futures import ThreadPoolExecutor

import urllib

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"}
v2ray_port = 10809
fengche_port = 20081
clash_port = 7890
port = clash_port
root_dir = r"./"


no_proxies = {}
real_proxies = {'http': f"http://127.0.0.1:{port}",
           'https': f"https://127.0.0.1:{port}"}
proxies = real_proxies
_uuid = uuid.uuid1().__str__()
# class SubtitleOcr():
#     def __init__(self, port) -> None:
#         pass
def get_token():
    url = r'https://web.baimiaoapp.com/api/perm/batch'
    res = requests.post(url=url,proxies=proxies,headers=headers)
    return ujson.loads(res.text)['data']['token']
def get_auth_token():
    url = r'https://web.baimiaoapp.com/api/user/login/anonymous'
    headers['x-auth-uuid'] = _uuid
    res = requests.post(url=url,proxies=proxies,headers=headers)
    return ujson.loads(res.text)['data']['token']
def push_tasks(token,start,count,batchId,files):
    pool = ThreadPoolExecutor(max_workers=10)
    task = []
    statusIds = []
    for i in range(start,start+count):
        filename = files[i-1]
        task.append(pool.submit(push_one_task,count,token,batchId,filename))
    for i in range(0,count):
        while (not task[i].done()):
            time.sleep(2)
        statusIds.append(task[i].result())
    pool.shutdown()
    return statusIds

def push_one_task(total,token,batchId,filename):
    # filename = root_dir+f'image-concat-%05d.jpg' % index
    ext = filename.split('.')[-1]
    with open(filename,'rb') as f:
        img = f.read()
    data = base64.b64encode(img).decode()
    img_data = f'data:image/{ext};base64,{data}'
    img_hash = md5(img).hexdigest()
    img_bytes = len(img)
    url = r'https://web.baimiaoapp.com/api/ocr/image/xunfei'
    
    data = {"batchId":batchId,"total":total,"token":token,"hash":img_hash,"name":filename,"size":img_bytes,"dataUrl":img_data,"result":{},"status":"processing","isSuccess":False}
    res = requests.post(url=url,proxies=proxies,headers=headers,data=data)
    statusId = ujson.loads(res.text)['data']['jobStatusId']
    return urllib.parse.quote_plus(statusId)
def get_results(ids):
    url = r'https://web.baimiaoapp.com/api/ocr/image/xunfei/status?jobStatusId='
    pool = ThreadPoolExecutor(max_workers=10)
    res_texts = []
    texts = []
    for id in ids:
        res_texts.append(pool.submit(get_one_result,url+id))
    for i in range(len(res_texts)):
        while (not res_texts[i].done()):
            time.sleep(2)
        texts.extend(res_texts[i].result())
    pool.shutdown()
    result = []
    [result.append(t) for t in texts if not t in result]
    return result
    
def get_one_result(url):
    lines = []
    while True:
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if ujson.loads(res.text)['data']['isEnded']:
            lines = ujson.loads(res.text)['data']['ydResp']['data']['lines']
            break;
        time.sleep(5)
    texts = []
    for l in lines:
        texts.append(l['text'])
    return texts
def do_ocr(files,output_path):
    try:
        # ocr = SubtitleOcr()
        print("正在获取认证token...")
        auth_token = get_auth_token()
        headers['x-auth-token'] = auth_token
        # print(auth_token)
        print("正在获取会话token...")
        token = get_token()
        # files = os.listdir(root_dir)
        # files = list(filter(lambda x : re.match(r'image-concat-\d{5}\.jpg',x), files))
        count = len(files)
        left = count
        i = 1
        statusIds = []
        while left > 0:
            batchSize = 50 if left >= 50 else left
            batchId = uuid.uuid1().__str__()
            print(f"正在执行batchSize为{batchSize}的OCR任务...")
            statusIds.extend(push_tasks(token,i,batchSize,batchId,files))
            i = i+batchSize
            left =left-batchSize
        print("所有OCR识别任务完成，正在获取结果...")
        texts = get_results(statusIds)
        print("正在写入txt文件...")
        with open(output_path+'.txt','w') as f:
            for t in texts:
                f.write(t)
                f.write('\n')
        return True
    except Exception as e:
        print(e)
        return False
    # print(texts)
    # print(token)
