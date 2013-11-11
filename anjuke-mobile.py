#! /usr/bin/env python
# -*- encoding: utf-8 -*-
# File: anjuke-mobile.py
# Desc: 抓取anjuke上的中介的手机号码

from bs4 import BeautifulSoup
import urllib2

import Queue
import threading
import time
import sqlite3
import sys

DEFAULT_DATABASE = "houseagent.sqlite"
DEFAULT_THREAD_NUMS = 1

navigator_page_prefix = "http://guangzhou.anjuke.com/sale/p"

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
        c.execute('''CREATE TABLE IF NOT EXISTS AGENT
             (number text unique, name text, company text, branch text)''')
        
        # 读取输入结果
        while True:
            item = out_queue.get()

            # 插入数据库
            try:
                c.execute("INSERT INTO AGENT VALUES (?, ?, ?, ?)", item)
                # 保存到硬盘
                conn.commit()
            except:
                print "Exception in inserting %s " % item

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
                                                    'Referer':"http://life.tenpay.com"})

                webpage = urllib2.urlopen(req)


                # 分析页面
                soup = BeautifulSoup(webpage.read())

                # 提取电话
                call_div = soup.find("div", { "class" : "A-fangyuan-call"})
                mobile = call_div.find("p").text.strip()
        
                agent_div = soup.find("div", { "class" : "A-fangyuan-agent"})
                agent = agent_div.find(id="broker_true_name")
                agent_name = agent.text.strip()

                # 提取其他
                lis = agent_div.find("ul").findAll("li")
                agent_company = lis[0].find_all('p')[1].text.strip()
                agent_sub_company = lis[1].find_all('p')[1].text.strip()

                # 去除空格
                mobile = "".join(mobile.split(" "))
        
                print "%s %s %s %s " % (mobile, agent_name, agent_company, agent_sub_company)
                self.out_queue.put((mobile, agent_name, agent_company, agent_sub_company))

            except:
                print "%s: exception" % self.name
            finally:
                print "%s: task done" % self.name
                self.queue.task_done()

if __name__ == '__main__':

    # 解析参数
    try:
        thread_nums = int(sys.argv[1])
    except:
        thread_nums = DEFAULT_THREAD_NUMS

    try:
        database = int(sys.argv[2])
    except:
        database = DEFAULT_DATABASE

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

    url = "%s%d" %(navigator_page_prefix, 1)

    req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser",
                                        'Referer':"http://life.tenpay.com"})

    webpage = urllib2.urlopen(req)


    # 分析页面
    soup = BeautifulSoup(webpage.read())

    # 提取房源信息链接
    root = soup.find(id = 'apf_id_12_list')
    
    lis = root.findAll('li')
    for li in lis:
        link = li.find("a")
        href = link.get("href").split("?")[0]
        print href

        # 填充队列
        queue.put(href)


    # 等待队列结束
    queue.join()
    out_queue.join()

    print "Exit..."
