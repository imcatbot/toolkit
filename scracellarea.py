#! /usr/bin/env python
# -*- encoding: utf-8 -*-
# File: scracellarea.py
# Author: Jiang Wei
# Desc: 爬取电话手机区号归属地主程序

import sys
import urllib2
from bs4 import BeautifulSoup
import sqlite3

import Queue
import threading

DEST="http://www.ip138.com:8080/search.asp?action=mobile&mobile="

class ThreadWork(threading.Thread):
    def __init__(self, out_queue, database):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        # 连接数据库
        self.database = database

    def run(self):
        conn = sqlite3.connect(self.database)
        c = conn.cursor()            
        # 读取输入结果
        while True:
            item = out_queue.get()

            # 插入数据库
            c.execute("INSERT INTO cells VALUES (?, ?, ?, ?)", item)
            # 保存到硬盘
            conn.commit()

            self.out_queue.task_done()
        


class ThreadUrl(threading.Thread):
    """
    线程
    """
    def __init__(self, queue, out_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue
        
    def run(self):
        while True:
            print "Start %s ...." % self.name
            num = self.queue.get()
        
            try:
                # 补足num的长度到标准手机号码
                new_num = "%d0123" % num
        
                url = "%s%s" % (DEST, new_num)
                # 获取查询结果
                req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser",
                                                'Referer':"http://www.ip138.com:8080"})

                webpage = urllib2.urlopen(req)

                #print webpage.read().decode("GBK")

                # 分析页面
                soup = BeautifulSoup(webpage.read())

                tables = soup.findAll('table')
                trs = tables[1].findAll('tr')
        
                # 属地
                tds = trs[2].findAll('td')
                area = tds[1].text

                # 卡类型
                tds = trs[3].findAll('td')
                cardtype = tds[1].text

                # 区号
                tds = trs[4].findAll('td')
                areacode = tds[1].text

                print "%s:%s %s %s" % (self.name, area, cardtype, areacode)
                # 插入数据库
                self.out_queue.put((num, area, cardtype, areacode))

            finally:
                print "%s: task done" % self.name
                self.queue.task_done()
        
if __name__ == '__main__':
    start_num = int(sys.argv[1])
    en_num    = int(sys.argv[2])

    print "From %d to %d" % (start_num, en_num)

    # 连接数据库
    database = "example.db"
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # 创建表
    c.execute('''CREATE TABLE IF NOT EXISTS cells
             (number text unique, area text, cardtype text, areacode text)''')

    queue = Queue.Queue()
    out_queue = Queue.Queue()
    
    # 开始分析线程
    for i in range(1):
        t = ThreadUrl(queue, out_queue)
        t.setDaemon(True)
        t.start()
        
    # 开始写入数据库线程
    t = ThreadWork(out_queue, database)
    t.setDaemon(True)
    t.start()
    
    # 遍历
    for num in range(start_num, en_num + 1):

        # 检查是否已存在，如是，忽略
        t = (num,)
        rows = c.execute("SELECT * FROM cells where number=?", t)

        old_num= rows.fetchone()

        if old_num != None:
            print "号码%s已经存在, 忽略..." % num
            continue

        queue.put(num)

    # 关闭连接
    conn.close()

    # 等待队列结束
    queue.join()
    out_queue.join()

    

    print "Exit..."
