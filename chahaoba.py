#! /usr/bin/env python
# -*- encoding: utf-8 -*-
# File: chahaoba.py
# Desc: 抓取chahaoba.com上的骗子的手机和固话号码

from bs4 import BeautifulSoup
import urllib2

import Queue
import threading
import time
import sqlite3
import sys
import re

DEFAULT_DATABASE = "chahaoba.sqlite"
DEFAULT_THREAD_NUMS = 1
DEFAULT_FORCE = False
SITE_PREFIX = "http://www.chahaoba.com/"

thief_comments = ['告诉你中了大奖，需要交公证费、邮寄费等',
                  '只响一声就挂断的来电，引诱回拨骗话费',
                  '代为投资理财黄金、期货等，承诺高额回报',
                  '股市骗子，黑嘴乱说',
                  '超低价推荐商品，货到付款，骗取定金',
                  '冒充银行通知，让你透露卡号、密码等信息',
                  '冒充法院、检察院、公安局等机关，监管你的银行账户',
                  '冒充电信运营商，说你电话欠费',
                  '直接发短信让你汇款',
                  '故意混淆电话区号的位数，让人弄错电话来源',
                  '用个人绑定号码、小灵通、新手机号段假冒本地电话',
                  '用恶意软件修改来电显示号码诈骗钱财',
                  '谎称家人生病、发生车祸、钱包丢失等',
                  '装熟人、套近乎，再找你借钱',
                  '谎称工作机会、招聘面试',
                  '谎称招生入学、解决就业',
                  '骗人参与传销',
                  '骗子模拟小孩哭腔扬言撕票骗家长',
                  '假冒政府高官、部队将军',
                  '推销纪念币、税法书籍',
                  '通知你涉嫌嫖娼，要缴纳罚款，否则通知家人、单位 ',]

class ThreadWork(threading.Thread):
    def __init__(self, out_queue, database):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        # 连接数据库
        self.database = database

    def run(self):
        conn = sqlite3.connect(self.database)
        conn.text_factory = str

        c = conn.cursor()            
        # 创建表,如果不存在
        c.execute('''CREATE TABLE IF NOT EXISTS phone
             (number text unique, comment text)''')
        
        # 读取输入结果
        while True:
            item = out_queue.get()
            item1 = tuple(item[:-1])
            item2 = (item[-1],)

            number = item[0]
            # 检查number是否已经在历史记录中
            t = (number,)
            rows = c.execute("SELECT * FROM history where number=?", t)
                
            old_url= rows.fetchone()
            
            exist = False
            if old_url != None:
                exist = True
            
            # 如果已经存在，并且不强制刷新，则忽略
            if exist == True:
                print "%s 已存在，忽略" % number
                self.out_queue.task_done()
                continue

            # 插入数据库
            try:
                c.execute("INSERT INTO phone VALUES (?, ?)", item1)
                # 保存到硬盘

            except Exception,data:
                print "Exception in inserting data:%s" % data

            try:
                # 保存历史
                c.execute("INSERT INTO history VALUES (?)", item2)

            except Exception,data:
                print "Exception in inserting history: %s" % data

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
                                                    'Referer':"http://www.chahaoba.com"})

                webpage = urllib2.urlopen(req)
                

                # 分析页面
                #print webpage.read()
                soup = BeautifulSoup(webpage.read())

                # 提取评论
                links = soup.find_all('a')

                for link in links:
                    #print "link", link
                    text = link.get_text().strip()
                    number = text.replace("-", "")

                    # 检查号码合法性
                    p = re.compile("^[0-9]+$")
                    if p.match(number) is None:
                        print "无效号码:%s" % number.encode("utf-8")
                        continue

                    comment = "揭露该骗子，提醒网友提高警惕！"
                    
                    print "%s %s" % (number.encode('utf-8'), comment)
                    number = number.encode('utf-8')
                    
                    self.out_queue.put([number, comment, number])

            except Exception,data:
                print "%s: exception: %s" % (self.name, data)
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
                                        'Referer':"http://www.chahaoba.com"})

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

    try:
        start_url = sys.argv[4]
    except:
        start_url = "http://www.chahaoba.com/%E9%AA%97%E5%AD%90%E5%8F%B7%E7%A0%81"


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

    # 获取手机号码页
    req = urllib2.Request(start_url, headers={'User-Agent' : "Magic Browser",
                                        'Referer':"http://www.chahaoba.com"})

    webpage = urllib2.urlopen(req)
                
    # 分析页面
    soup = BeautifulSoup(webpage.read())

    # 提取评论
    links = soup.find_all('a')

    for link in links:
        href = link.get("href")
        if href is None:
            continue
        
        last_word = href.split("/")[-1][-6:].encode("utf-8")
        if last_word == "%AD%90":
            href = "http://www.chahaoba.com/" + href
            print "link=", href
            queue.put(href)

    # 填充队列
    queue.put(start_url)

#    sys.exit(0)

    conn2.close()
    # 等待队列结束
    queue.join()
    out_queue.join()

    print "Exit..."
