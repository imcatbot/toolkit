#! /usr/bin/env ruby
# -*- coding: utf-8 -*-

require 'rubygems'
require 'mechanize'
require 'sqlite3'

# 获取指定的链接对象,且只返回一个
def get_page_link(links, href)
  links.each do |link|
    if link.href == href
      return link
    end
  end
end

# 主函数
if __FILE__ == $0

  db = SQLite3::Database.new("52longxi.history")

  agent = Mechanize.new  
  page = agent.get('http://www.52longxi.com')

  # 获取登录表单
  login_form = page.forms.first()

  # 从文件读取随机用户
  lines = []
  File.open(ARGV[0], "r") do |file|
    while line = file.gets
      # 添加前去换行符号
      lines.push(line.chomp)
    end
  end

  user = lines.sample
  
  login_form.username = user.split[0]
  login_form.password = user.split[1]
  
  puts "用户:%s" % [user.split[0]]
  page = agent.submit(login_form)
  
  plates = []
  # 找出所有的板块
  page.links.each do |link|
    next if link.href() !~ /fid=[0-9]+$/

    #忽略两个特定的板块51和52
    next if link.href() =~ /fid=5[12]$/
    
    # 如果没有，就添加
    if !plates.member?(link)
      plates.push(link)
    end
    
  end

  # 随机在三个论坛发帖
  3.times.each do |x|
    plate = plates.sample
    
    page = plate.click()

    sub_page = page.search('table#threadlisttableid')
    tbodies = sub_page.search('tbody')

    # 遍历每个主题
    tbodies.each do |tbody|
      next if tbody["id"] !~ /normalthread_[0-9]+/
      th = tbody.search("th")[0]
      link = th.search("a")[1]
      author = tbody.search("cite").search("a")[0].text
      
      me = user.split[0]
      # 检查历史记录，如果'我'已经连续3次回帖，则跳过
      times = db.get_first_value( "select times from history where href=? and author=?", 
                                  link["href"],
                                  me)
      if times == nil
        db.execute("insert into history values (?, ?, ?)",
                   link["href"],
                   me,
                   0)
        # 重新赋值为0
        times = 0
      end
      
      # 如果me已经连续发布3次，忽略该主题
      if times >= 1 and me == author
        puts "%s[%d] -- %s, 忽略!" % [author, times, me]
        next
      end
      
      # 睡眠2分钟
      print "睡眠2分钟..."
      sleep(60*2)
      puts "!"

      # 获取链接对象
      link_obj = get_page_link(page.links, link["href"])
      
      subject_page = link_obj.click()
      
      # 读取随机内容
      lines = []
      File.open(ARGV[1], "r") do |file|
        while line = file.gets
          lines.push(line)
        end
      end

      msg = lines.sample
        
      # 获取快速回帖表单
      puts "回复:[%s][%s] --> %s" % [plate.text, link.text[0..20], msg[0..20]]
      
      fast_postform = subject_page.forms_with(:id=>"fastpostform").first()
      fast_postform.message = msg
      agent.submit(fast_postform)

      # 记录,如果上一次不是'我'回帖，则计数为1,否则，累加1
      if me != author
        db.execute("update history set times=1 where href=? and author=?", 
                   link["href"],
                   me)
      else
        db.execute("update history set times=times+1 where href=? and author=?", 
                   link["href"],
                   me)
      end

    end
    
  end

end
