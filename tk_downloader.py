# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 11:30:35 2021

@author: ctong
"""

import json
import requests
import hashlib
import getpass
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod

'''
15850786173
qwertyUIOP
'''

class Strategy(metaclass = ABCMeta):
    '''策略虚基类'''
    @abstractmethod
    def execute(self, data):
        return ''
    
    def get_content(self, data):
        '''获取题干信息'''
        soup =  BeautifulSoup(data['content'], 'lxml')
        txt = ''
        for p in soup.find_all('p'):
            txt += p.text
        txt += '\n'
        return txt

    
class zgtStrategy(Strategy):
    '''主观题策略'''
    def execute(self, data):
        return self.get_content(data)
        

class sftStrategy(Strategy):
    '''是非题策略'''
    def execute(self, data):
        txt = self.get_content(data)
        for opt in data['option']:
            t_add = opt['value']
            if opt['class'] == 'current':
                t_add += '\ttrue'
            txt += t_add + '\n'
        return txt


class tktStrategy(Strategy):
    ''''填空题策略'''
    def execute(self, data):
        txt = self.get_content(data)
        txt += str(data['answer']) + '\n'
        return txt


class strategyFactory:
    '''策略工厂'''
    def create_strategy(self, s):
        if s == '主观题':
            return zgtStrategy()
        elif s == '单选题':
            return sftStrategy()
        elif s == '多选题':
            return sftStrategy()
        elif s == '数值题':
            return tktStrategy()
        elif s == '填空题':
            return tktStrategy()
        elif s == '是非题':
            return sftStrategy()
        elif s == '综合题':
            raise TypeError("综合题类型没有相关方法，请自行补充")
        else:
            raise TypeError("No such type named %s" % s)


class tkDownloader:
    '''题库下载器'''
    def __init__(self, data, cid):
        self.session = requests.session()
        self.cid = cid
        headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'}
        url = 'https://teaching.applysquare.com/Api/User/ajaxLogin'
        r = self.session.post(url, data = data, headers = headers)
        dic = json.loads(r.content.decode('utf-8'))
        self.token = dic['message']['token']
        self.uid = dic['message']['uid']
    
    def get_url(self, p):
        url = 'https://teaching.applysquare.com/Api/Question/getAllQuestion/token/' + self.token + \
            '?is_exam=&is_practice=&is_work=&cid=' + self.cid + \
            '&page=' + str(p) + '&status=&type=0&keyword=&sort=&sort_filed=&first_jump=1&answer_type=0&uid=' \
            + self.uid
        return url

    def get_n_pages(self):
        '''获取总页数'''
        p = 1
        url = self.get_url(p)
        r = self.session.get(url)
        dic = json.loads(r.content.decode('utf-8'))
        return dic['message']['all_page']
    
    def download_page(self, p, f):
        '''按页下载'''
        url = self.get_url(p)
        r = self.session.get(url)
        dic = json.loads(r.content.decode('utf-8'))
        q_id = 0
        sf = strategyFactory()
        for question in dic['message']['list']:
            try:
                s = sf.create_strategy(question['real_type'])
                txt = s.execute(question)
                f.write(str(q_id + 1 + (p - 1) * 10) + '. ' + txt + '\n\n')
            except:
                print('no.' + str(q_id + 1 + (p - 1) * 10) + question['real_type'])
            q_id += 1
    
    def run(self):
        '''执行'''
        pages = self.get_n_pages()
        f = open('题库.txt', 'a+', encoding = 'utf-8')
        for p in range(1, pages + 1):
            print('page ' + str(p))
            self.download_page(p, f)
        f.close()
        
        
if __name__ == "__main__":
    cid = '16543'
    data = {'email':'', 'password':''}
    data['email'] = input("email:")
    m = hashlib.md5()
    password = getpass.getpass("password:")
    m.update(password.encode())
    data['password'] = m.hexdigest()
    
    tk_downloader = tkDownloader(data, cid)
    tk_downloader.run()
    