# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 10:05:46 2019

@author: ctong
"""

import json
import requests
import hashlib
import getpass
import pandas as pd
import time
import numpy as np


session = requests.session()
day_len = 60 * 60 * 24
def log_in(data):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
    url = 'https://teaching.applysquare.com/Api/User/ajaxLogin'
    r = session.post(url, data = data, headers = headers)
    dic = json.loads(r.content.decode('utf-8'))
    return (dic['message']['token'], dic['message']['uid'])
           
def cal_d(s_time, a_time):
    s = time.mktime(time.strptime(s_time, "%Y-%m-%d %H:%M"))
    a = time.mktime(time.strptime(a_time, "%Y-%m-%d %H:%M"))
    return (a - s) // day_len + 1   #不足一天按一天计算
 
if __name__ == "__main__":
    cid = '4663'
    check_submit_late = True
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
    
    data = {'email':'', 'password':''}
    data['email'] = input("email:")
    m=hashlib.md5()
    password = getpass.getpass("password:")
    m.update(password.encode())
    data['password'] = m.hexdigest()
    token, uid = log_in(data)
    df1 = pd.DataFrame({'id':[],'name':[]})#签到
    df2 = pd.DataFrame({'id':[],'name':[]})#作业提交
    
    url = 'https://teaching.applysquare.com/Api/Score/getScoreList/token/' + token + \
              '?p=1&keyword=&uid=' + uid + '&cid=' + cid
    r = session.get(url)
    dic = json.loads(r.content.decode('utf-8'))
    pages = dic['message']['pages']
    
    for i in range(1, pages + 1):
        print(i)
        url = 'https://teaching.applysquare.com/Api/Score/getScoreList/token/' + token + \
              '?p=' + str(i) + '&keyword=&uid=' + uid + '&cid=' + cid
        r = session.get(url)
        dic = json.loads(r.content.decode('utf-8'))
        for student in dic['message']['item']:
            df1 = df1.append({'id':student['student_id'], 'name':student['realname']}, ignore_index=True)
            df2 = df2.append({'id':student['student_id'], 'name':student['realname']}, ignore_index=True)
            be_uid = student['uid']
            
            url_qd = 'https://teaching.applysquare.com/Api/Score/getSignItems/token/' + token + \
                     '?uid=' + be_uid + '&cid=' + cid
            rqd = session.get(url_qd, headers = headers)
            dicqd = json.loads(rqd.content.decode('utf-8'))
            for qd in dicqd['message']['items']:
                if not qd['format_event_begin_time'] in df1.keys():
                    df1[qd['format_event_begin_time']] = len(df1) * ['']
                if qd['format_answer_time'] != '1970-01-01 08:00:00':
                    t1 = time.mktime(time.strptime(qd['format_event_begin_time'], "%Y-%m-%d %H:%M:%S"))
                    t2 = time.mktime(time.strptime(qd['format_answer_time'], "%Y-%m-%d %H:%M:%S"))
                    if t2 - t1 <= day_len:  #签到时间晚了1天以内
                        df1.loc[len(df1) - 1, qd['format_event_begin_time']] = 1
                    else:
                        df1.loc[len(df1) - 1, qd['format_event_begin_time']] = 0
                else:
                    df1.loc[len(df1) - 1, qd['format_event_begin_time']] = 0
            
            url_zy = 'https://teaching.applysquare.com/Api/Score/getHomeworkItems/token/' + token + \
                     '?uid=' + be_uid + '&cid=' + cid
            rzy = session.get(url_zy, headers = headers)
            diczy = json.loads(rzy.content.decode('utf-8'))
            for zy in diczy['message']['items']:
                if not zy['homework_title'] in df2.keys():
                    df2[zy['homework_title']] = len(df2) * [np.nan]
                orinum = df2[zy['homework_title']][len(df2) - 1]
                df2.loc[len(df2) - 1, zy['homework_title']] = np.nanmax([int(zy['is_answer']), orinum])
    
    if check_submit_late:
        url = 'https://teaching.applysquare.com/Api/Work/getPublishList/token/' + token +'?p=1&sort_order=publish_at&sort=DESC&plan_id=-1&uid=' + uid + '&cid=' + cid
        r = requests.get(url, stream=True, timeout=60)
        dic = json.loads(r.content.decode('utf-8'))
        totalPages = dic['message']['totalPages']
        #hwdic = {}
        for i in range(1, totalPages + 1):
            url = 'https://teaching.applysquare.com/Api/Work/getPublishList/token/' + token +'?p=' + str(i) + '&sort_order=publish_at&sort=DESC&plan_id=-1&uid=' + uid + '&cid=' + cid
            r = requests.get(url, stream=True, timeout=60)
            dic = json.loads(r.content.decode('utf-8'))
            for hw in dic['message']['rows']:
                #hwdic[hw['title']] = hw[]
                df2[hw['title']] -= 1
                #先这么写吧.交的是0，没交的是-1
                print(hw['title'] + hw['submit_at'])
                
                
                url = 'https://teaching.applysquare.com/Api/Work/getTeacherNotReviewList/token/' + token + '?homework_id=' + hw['homework_id'] + '&cid=' + cid + '&page=1&search_key=&uid=' + uid
                r = requests.get(url, stream=True, timeout=60)
                sdic = json.loads(r.content.decode('utf-8'))
                pages = int(sdic['message']['count'] / 10) + 1
                for page in range(1, pages + 1):
                    url = 'https://teaching.applysquare.com/Api/Work/getTeacherNotReviewList/token/' + token + '?homework_id=' + hw['homework_id'] + '&cid=' + cid + '&page='  + str(page) + '&search_key=&uid=' + uid
                    r = requests.get(url, stream=True, timeout=60)
                    pydict = json.loads(r.content.decode('utf-8'))
                    for student in pydict['message']['not_review_list']:
                        if student['is_delay']:
                            for indx in np.where(df2['name'] == student['realname']):
                                #df2.loc[indx,hw['title']] = 0.5
                                ssurl = 'https://teaching.applysquare.com/Api/Work/getWorkSubmitList/token/' + token + '?homework_id=' + hw['homework_id'] + '&be_uid=' + student['uid'] + '&uid=' + uid + '&cid=' + cid
                                r = requests.get(ssurl, stream=True, timeout=60)
                                zzydict = json.loads(r.content.decode('utf-8'))
                                answer_time = zzydict['message']['rows'][0]['answer_time']
                                delay_time = cal_d(hw['submit_at'], answer_time)
                                df2.loc[indx,hw['title']] = delay_time
                                print(student['realname'] + answer_time + '\t' + str(delay_time))
                                
                                
    df22 = df2.groupby(by = 'id').max()
    df11 = df1.groupby(by = 'id').max()#相同学号处理，原始数据可见df1&&df2

    df11.to_csv('qd11.csv', encoding = 'utf-8-sig')
    df22.to_csv('zy22.csv', encoding = 'utf-8-sig')
