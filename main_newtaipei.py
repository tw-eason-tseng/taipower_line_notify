#-*- coding:utf-8 -*-
import requests
import re
import os
import sys
import ddddocr
import configparser
from bs4 import BeautifulSoup
ocr = ddddocr.DdddOcr()
config = configparser.ConfigParser()
config.read("config.ini")
_url = "https://ebpps2.taipower.com.tw"

_custNo=config["Power"]["custNo"]

## token 要改
token = config["Line"]["token"]
headers = {
    "Authorization": "Bearer " + token, 
    "Content-Type" : "application/x-www-form-urlencoded"
}

s = requests.session()
s.headers.update({'User-Agent':'Mozilla/5.0 (compatible; Konqueror/4.3; Linux 2.6.31-16-generic; X11) KHTML/4.3.2 (like Gecko)'})
r = s.get(f"{_url}/simplebill/simple-query-bill")
if r.ok :
    #print(r.cookies.get_dict())
    s.headers.update({"Referer":"https://ebpps2.taipower.com.tw/simplebill/simple-query-bill"})
    r_img = s.get(f"{_url}/captcha/captImg/captcha.png")
    #print(r_img.status_code)
    #print(r_img.text)
    if r_img.ok:
        soup = BeautifulSoup(r.text,'lxml')
        get_r_csrf = soup.find("meta",attrs={"name":"_csrf"})["content"]
        print(get_r_csrf)
        #print(r_img.cookies.get_dict())
        with open("image.png","wb") as f:
            f.write(r_img.content)
        res = ocr.classification(r_img.content)
        print(res)
        post_data = {
            "_csrf":get_r_csrf,
            "custNo":_custNo,
            "answer":res,
            "email":"",
            "Search":"%E6%9F%A5%E8%A9%A2"
                }
        r_query = s.post(f"{_url}/simplebill/post-simple-query-bill",data=post_data)
        if r_query.ok:
            print(r_query.status_code)
            #print(r_query.text)
            query_soup = BeautifulSoup(r_query.text,'lxml')
            get_data = query_soup.find("table",{"class":"mobile_search_list"}).find_all("td",{"class":"aCenter"})
            get_mounth = get_data[0].text
            get_status = get_data[1].text

            print(get_mounth.strip())
            print(get_status.strip())
            if (get_status.strip().find("已繳") >= 0):
                print("[Info]已繳費用")
            elif (get_status.strip().find("扣繳中") >= 0):
                print("[Info]扣繳中")
            else:
                print("[Info]提醒沒繳費")
            post_data_2 = {
                    "_csrf":get_r_csrf,
                    "custNo":_custNo,
                    "billName":config["Power"]["name"],
                    "Search":"查詢明細"}
            r_json_query = s.post(f"{_url}/simplebill/post-simple-query-billdetail",data=post_data_2)
            if r_json_query.ok:
                info_message = ""
                print(r_json_query.status_code)
                query_json_soup = BeautifulSoup(r_json_query.text,'lxml')
                get_info_tables = query_json_soup.find_all("table",{"class":"table_list2"})[2]
                get_info_tables2 = query_json_soup.find_all("table",{"class":"table_list2"})[3]
                get_info_node = get_info_tables.find_all("th"),get_info_tables.find_all("td")
                get_info_node2 = get_info_tables2.find_all("th"),get_info_tables2.find_all("td")
                for query_range in range(len(get_info_node[0])):
                    info_message += f"{get_info_node[0][query_range].text.strip()} {get_info_node[1][query_range].text.strip()} \n"
                    print(f"{get_info_node[0][query_range].text.strip()} {get_info_node[1][query_range].text.strip()} "   )
                for query_range in range(len(get_info_node2[0])):
                    info_message += f"{get_info_node2[0][query_range].text.strip()} {get_info_node2[1][query_range].text.strip()} \n"
                    print(f"{get_info_node2[0][query_range].text.strip()} {get_info_node2[1][query_range].text.strip()} "   )
                payload = {'message': info_message }
                r_line = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
                print(r_line.status_code)


else:
    print(r.status_code)
    print("有問題")
