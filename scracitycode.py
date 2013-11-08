#! /usr/bin/env python
# -*- encoding: utf-8 -*-
# File: scracitycode.py
# Author: Jiang Wei
# Desc: 爬取各个城市的电话区号主程序

import sys
import urllib2
from bs4 import BeautifulSoup
import sqlite3

import Queue
import threading
import time

class ThreadSohao(threading.Thread):
    """
    分析http://www.sohao.org/quhao.html的城市电话区号
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.dest = "http://www.sohao.org/quhao.html"

    def run(self):
        print "Start %s ...." % self.name
        url = self.dest

        # 连接数据库
        database = "example.db"
        conn = sqlite3.connect(database)
        c = conn.cursor()

        # 创建表
        #c.execute('''CREATE TABLE IF NOT EXISTS citycode
        #    (province text, city text, code text)''')
        c.execute('''CREATE TABLE IF NOT EXISTS cells
             (number text unique, area text, cardtype text, areacode text)''')

        
        # 获取查询结果
        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser",
                                            'Referer':"http://www.sohao.org"})
        
        webpage = urllib2.urlopen(req)


        # 分析页面
        soup = BeautifulSoup(webpage.read())

        root = soup.find('table')

        rows = root.findAll('tr')
        province = ""
        for row in rows:
            tds = row.findAll('td')
            if tds[0].text.strip().encode("utf-8").count('电话区号') > 0:
                index = tds[0].text.strip().encode("utf-8").find('电话区号')
                province = tds[0].text.strip()[:-4]
                
            else:
                i = 0
                while i < len(tds):
                    if tds[i].text.strip() != "":
                        city = tds[i].text.strip()
                        code = tds[i+1].text.strip()
                        print "%s %s %s" % (province, tds[i].text.strip(), tds[i+1].text.strip())
                        # 插入数据库
                        item = (code, "%s %s" % (province, city), "", "")
                        c.execute("INSERT INTO cells VALUES (?, ?, ?, ?)", item)
                        
                    i += 2
        # 保存到硬盘
        conn.commit()

        
if __name__ == '__main__':
    # 开始分析线程
    t = ThreadSohao()
    t.start()
    t.join()

    print "Exit..."
