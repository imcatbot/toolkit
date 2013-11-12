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
DEFAULT_FORCE = False

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
        c.execute('''CREATE TABLE IF NOT EXISTS agent
             (number text unique, name text, company text, branch text, city text)''')
        
        # 读取输入结果
        while True:
            item = out_queue.get()
            item1 = tuple(item[:-1])
            item2 = (item[-1],)

            # 插入数据库
            try:
                c.execute("INSERT INTO agent VALUES (?, ?, ?, ?, ?)", item1)
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
                
                # 从url提取城市
                city = url.split(".")[0].split("//")[1]

                print "%s %s %s %s %s" % (mobile, agent_name, agent_company, agent_sub_company, city)
                self.out_queue.put([mobile, agent_name, agent_company, agent_sub_company, city, url])

            except:
                print "%s: exception" % self.name
            finally:
                print "%s: task done" % self.name
                self.queue.task_done()

def get_soup_object(url):
    """
    返回beautifulsoup的实例
    """
    obj = None

    req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser",
                                        'Referer':"http://life.tenpay.com"})

    webpage = urllib2.urlopen(req)

    # 分析页面
    obj = BeautifulSoup(webpage.read())
    
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
             (url text unique)''')
    
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

    # 获取城市列表
    city_url = "http://www.anjuke.com/index/"

    soup = get_soup_object(city_url)

    links = soup.find(id="location").find_all("a")

    hot_city_links = []
    cold_city_links = []
    # 热门城市
    for link in links:
        hot_city_links.append(link.get("href"))
        
    links = soup.find("div", {"class": "cities_boxer"}).find_all("a")
    # 所有城市(不包括热门城市)
    for link in links:
        if hot_city_links.count("%s/" % link.get("href")) == 0:
            cold_city_links.append("%s/" % link.get("href"))

    #热门城市查前面20页，冷门城市查前5页
    urls = []
    for c in hot_city_links:
        for p in range(1, 21):
            url = "%s/sale/p%d" % (c, p)
            urls.append(url)
    
    for c in cold_city_links:
        for p in range(1, 6):
            url = "%s/sale/p%d" % (c, p)
            urls.append(url)

    # 遍历所有链接
    for url in urls:
        # 分析页面
        soup = get_soup_object(url)
    
        # 提取房源信息链接
        root = soup.find(id = 'apf_id_12_list')
        if root is None:
            continue

        lis = root.findAll('li')
        for li in lis:
            link = li.find("a")
            href = link.get("href").split("?")[0]

            # 检查href是否已经在历史记录中
            t = (href,)
            rows = c2.execute("SELECT * FROM history where url=?", t)

            old_url= rows.fetchone()
            
            exist = False
            if old_url != None:
                exist = True
            
            # 如果已经存在，并且不强制刷新，则忽略
            if exist == True and force == False:
                print "%s 已存在，忽略" % href
                continue

            # 填充队列
            queue.put(href)

#            break

    conn2.close()
    # 等待队列结束
    queue.join()
    out_queue.join()

    print "Exit..."
