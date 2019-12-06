#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mark: 根据服务器sn号查询DELL服务器型号、出厂时间、过保时间

import requests,re,time
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import threading
import json

base_url = 'https://www.dell.com/support/home/cn/zh/cnbsd1/product-support/servicetag/'

# 根据sn号获取返回页面
def Get_Page(url):
    try:
        header = {'Connection': 'keep-alive','Pragma': 'no-cache','Cache-Control': 'no-cache','Upgrade-Insecure-Requests': '1',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36', 
                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3' ,
                  'Sec-Fetch-Site': 'none' ,'Sec-Fetch-Mode': 'navigate','Accept-Encoding': 'gzip, deflate, br' ,
                  'Accept-Language': 'zh-CN,zh;q=0.9'}
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None

def Date2Date(date):
    date = date.strip()
    timeArray = time.strptime(date, "%d %m月 %Y")
    otherStyleTime = time.strftime("%Y/%m/%d", timeArray)
    return otherStyleTime

# 根据返回码，获取信息
def Get_Info(s_code,sn):
    header = {'Connection': 'keep-alive','Pragma': 'no-cache','Cache-Control': 'no-cache','Upgrade-Insecure-Requests': '1',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36', 
                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3' ,
                  'Sec-Fetch-Site': 'none' ,'Sec-Fetch-Mode': 'navigate','Accept-Encoding': 'gzip, deflate, br' ,
                  'Accept-Language': 'zh-CN,zh;q=0.9'}
    url_params = {"serviceTag":s_code}

    #需要先获取Cookie,否则Access Denied
    cookie_url = "https://www.dell.com/support/home/cn/zh/cnbsd1/product-support/servicetag/%s/overview" % (s_code)
    cookie_res = requests.get(cookie_url, headers=header)
    cookies = requests.utils.dict_from_cookiejar(cookie_res.cookies)

    info_url = 'https://www.dell.com/support/components/dashboard/cn/zh/cnbsd1/Warranty/GetWarrantyDetails'
    # postman模拟请求时要带参数,否则可能是404
    r1 = requests.post(info_url,data=url_params,headers=header,cookies=cookies)
    h1 = r1.text
    
    soup = BeautifulSoup(h1,"html.parser")
    printContent = soup.select('#printContent')

    data = printContent[0].find_all("tr")
    data_len = len(data)

    info = data[1].find_all("b")
    shippingDate = Date2Date(info[1].next_element.split(":")[1])
    country = info[2].next_element.split(":")[1].strip()
    hddSystemDescription = BeautifulSoup(cookie_res.text,"html.parser").select("#hddSystemDescription")[0].next_element

    for i in range(3,data_len):
        d = data[i].find_all("td")
        ServiceType = d[0].next_element
        ServiceStartTime = Date2Date(d[1].next_element)
        ServiceEndTime = Date2Date(d[2].next_element)
        text = "| %s | %s | %s | %s | %s | %s | %s |\n" % (sn,shippingDate,country,hddSystemDescription,ServiceType,ServiceStartTime,ServiceEndTime)
        write_data(text)

   

def write_data(data):
    with open('./snlist.txt', 'a', encoding='utf-8') as ff:
        ff.write(data)

class DELLINFO():

    # 主程序
    def Get_Dellinfo(self,sn):
        html1 = Get_Page(base_url + sn)
        if html1:
            p1 = re.compile('servicetag/(.*)/overview"')
            r1 = p1.findall(html1)  
            Get_Info(r1[0],sn)

if __name__=='__main__':
    t_list = []
    sn_list = []
    pool = ThreadPoolExecutor(10)
    dinfo = DELLINFO()

    with open('./snlist.txt', 'w', encoding='utf-8') as ff:
        title = "|SN|发货日期|国家|型号|服务类型|开始时间|结束时间|\n"
        ff.write(title)

    with open('./sn.txt','r',encoding='utf-8') as f:
        for i in f.read().splitlines():
            sn_list.append(i.strip())
            t = threading.Thread(target=dinfo.Get_Dellinfo, args=(i.strip(),))
            t_list.append(t)
            t.start()
        for t in t_list:
            t.join()
