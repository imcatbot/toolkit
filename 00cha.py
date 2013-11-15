#! /usr/bin/env python
# -*- encoding: utf-8 -*-
# File: 00cha.py
# Desc: 抓取00cha.com上的中介的手机和固话号码

from bs4 import BeautifulSoup
import urllib2

import Queue
import threading
import time
import sqlite3
import sys

DEFAULT_DATABASE = "00cha.sqlite"
DEFAULT_THREAD_NUMS = 1
DEFAULT_FORCE = False
SITE_PREFIX = "http://www.00cha.com/"

class ThreadWork(threading.Thread):
    def __init__(self, out_queue, database):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        # 连接数据库
        self.database = database

    def run(self):
        conn = sqlite3.connect(self.database)
        c = conn.cursor()            
        # 创建表,如果不存在
        c.execute('''CREATE TABLE IF NOT EXISTS phone
             (number text unique, comment text)''')
        
        # 读取输入结果
        while True:
            item = out_queue.get()
            item1 = tuple(item[:-1])
            item2 = (item[-1],)

            # 插入数据库
            try:
                c.execute("INSERT INTO phone VALUES (?, ?)", item1)
                # 保存到硬盘

            except:
                print "Exception in inserting data"

            try:
                # 保存历史
                c.execute("INSERT INTO history VALUES (?)", item2)

            except:
                print "Exception in inserting history"

            conn.commit()
            self.out_queue.task_done()

class ThreadFetcher(threading.Thread):
    """
    分析页面线程
    """
    def __init__(self, queue, out_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue

    def run(self):
        while True:
            print "Start %s ...." % self.name
            url = self.queue.get()

            try:
                req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser",
                                                    'Referer':"http://www.00cha.com"})

                webpage = urllib2.urlopen(req)
                

                # 分析页面
                soup = BeautifulSoup(webpage.read())

                # 提取评论
                comment_div = soup.find("div", { "class" : "fp"})
                lis = comment_div.find("ul").find_all("li")

                comment = lis[0].get_text().strip()
                date = lis[0].font.get_text()
                publisher = lis[0].i.get_text()

                date_len = len(date)
                publisher_len = len(publisher)
                print "-----------------", comment[date_len:-publisher_len]
                comment = comment[date_len:-publisher_len]
                
                # 从url提取城市
                number = url.split("t=")[-1]

                print "%s %s" % (number, comment)
                self.out_queue.put([number, comment, number])

            #except:
            #    print "%s: exception" % self.name
            finally:
                print "%s: task done" % self.name
                self.queue.task_done()

def get_soup_object(url):
    """
    返回beautifulsoup的实例
    """
    obj = None

    try:
        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser",
                                        'Referer':"http://www.00cha.com"})

        webpage = urllib2.urlopen(req)
        
    # 分析页面
        obj = BeautifulSoup(webpage.read())
    except:
        print "Fetch url error"

    return obj


if __name__ == '__main__':

    # 解析参数
    try:
        thread_nums = int(sys.argv[1])
    except:
        thread_nums = DEFAULT_THREAD_NUMS

    try:
        database = sys.argv[2]
    except:
        database = DEFAULT_DATABASE

    try:
        force = int(sys.argv[3]) > 0
    except:
        force = DEFAULT_FORCE

    # 初始化历史数据库
    conn2 = sqlite3.connect(database)
    c2 = conn2.cursor()            
    # 创建表,如果不存在
    c2.execute('''CREATE TABLE IF NOT EXISTS history
             (number text unique)''')
    
    # 初始化队列
    queue = Queue.Queue()
    out_queue = Queue.Queue()

    # 预先启动线程
    # 开始分析线程
    for i in range(thread_nums):
        t = ThreadFetcher(queue, out_queue)
        t.setDaemon(True)
        t.start()
        
    # 开始写入数据库线程
    t = ThreadWork(out_queue, database)
    t.setDaemon(True)
    t.start()

    # 获取手机号码列表
    url_prefix = ["http://www.00cha.com/pian.asp"]

    for prefix in url_prefix:
        for i in range(1, 2):
            mobile_index_url = prefix
            
            soup = get_soup_object(mobile_index_url)
            if soup is None:
                continue

            table = soup.find(id="table1")

            trs = table.find_all("tr")
            title = False
            for tr in trs:
                # 跳过第一行
                if title == False:
                    title = True
                    continue
                
                tds = tr.find_all("td")
                number_link = tds[0].find("a")
                if number_link is not None:
                    number_link = number_link.get("href")
                number = tds[0].text.strip()

                # 检查number是否已经在历史记录中
                t = (number,)
                rows = c2.execute("SELECT * FROM history where number=?", t)
                
                old_url= rows.fetchone()
            
                exist = False
                if old_url != None:
                    exist = True
            
                # 如果已经存在，并且不强制刷新，则忽略
                if exist == True and force == False:
                    print "%s 已存在，忽略" % number.encode("utf-8")
                    continue
                
                # 如果评论不完整，则进入详细页面
                comment = tds[1].text.strip()
                comment_link = tds[1].find("a")
                if comment_link is not None:
                    comment_link = "%s%s" % (SITE_PREFIX, comment_link.get("href"))
                    # 填充队列
                    queue.put(comment_link)
                else:
                    out_queue.put([number, comment, number])

#                print "%s %s %s" % (href, mobile, text)
#        break
#    sys.exit(0)

    conn2.close()
    # 等待队列结束
    queue.join()
    out_queue.join()

    print "Exit..."
