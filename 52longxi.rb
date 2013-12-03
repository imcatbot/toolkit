#! /usr/bin/env ruby
# -*- coding: utf-8 -*-

require 'rubygems'
require 'mechanize'
require 'sqlite3'

# 主函数
if __FILE__ == $0

  db = SQLite3::Database.new("52longxi.history")

  agent = Mechanize.new  
  page = agent.get('http://www.52longxi.com')

  # 获取登录表单
  login_form = page.forms.first()

  login_form.username = ARGV[0]
  login_form.password = ARGV[1]

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

  # 遍历论坛，如果有新贴，则回帖

  # 每个板块的第一页，如果该贴没有回复，则回复
  # 如果该贴的最后一个回复者是本人，且回复时间在2各小时内，则不回复
  # 每个贴尝试3次回复
  plates.each do |plate|
    page = plate.click()

    sub_page = page.search('table#threadlisttableid')
    tbodies = sub_page.search('tbody')

    # 遍历每个主题
    tbodies.each do |tbody|
      next if tbody["id"] !~ /normalthread_[0-9]+/
      th = tbody.search("th")[0]
      link = th.search("a")[1]
      author = tbody.search("cite").search("a")[0].text
      
      me = ARGV[0]
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
      next if times >= 3 and me == author

      # 睡眠2分钟
      sleep(60*2)

      page.links.each do |pl|
        next if pl.href != link["href"]
        # 跳转到该主题
        subject_page = pl.click()

        # 读取随机内容
        lines = []
        File.open(ARGV[2], "r") do |file|
          while line = file.gets
            lines.push(line)
          end
        end

        msg = lines.sample
        
        # 获取快速回帖表单
        puts "正在回复", link.text, msg
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
        break
      end
    end
    
  end

end
