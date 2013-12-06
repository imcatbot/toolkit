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

# 获取论坛
def get_forum_with_id(page, id)
  
end

# 读取随机内容(一行)
def get_random_content(file)
  article = {}
  lines = []
  File.open(file, "r") do |file|
    while line = file.gets
      lines.push(line)
    end
  end

  msg = lines.sample
  obj = msg.match(/<subject>([\W\w]+)<\/subject><content>([\W\w]+)<\/content>/)
  if obj != nil
    article["subject"] = obj.captures[0]
    article["content"] = obj.captures[1]
  end
  return article
end

# 从文件读取随机用户
def get_random_user(file)
  lines = []
  File.open(ARGV[0], "r") do |file|
    while line = file.gets
      # 添加前去换行符号
      lines.push(line.chomp)
    end
  end

  user = lines.sample
end

# 发表文章
def post_article(forum, user, article)
  page = forum.click()
  
  # 获取登录表单
  login_form = page.forms.first()
  
  login_form.username = user.split[0]
  login_form.password = user.split[1]
  
  agent = Mechanize.new  
  page = agent.submit(login_form)

  fast_postform = page.forms_with(:id=>"fastpostform").first()
  fast_postform.subject = article["subject"]
  fast_postform.message = article["content"]

  agent.submit(fast_postform)
  
end

# 主函数
if __FILE__ == $0

  db = SQLite3::Database.new("52longxi.history")

  agent = Mechanize.new  
  page = agent.get('http://www.52longxi.com')

  forum_ids = ARGV[2].split(',')
  
  forums = {}
  # 找出所有的板块
  page.links.each do |link|
    next if link.href() == nil

    match_obj = link.href().match(/fid=([0-9]+$)/)

    next if match_obj == nil

    forum_id = match_obj.captures[0]
    
    next if !forum_ids.member?(forum_id)
        
    forums[link.href] = link

  end
  
  forums.each do |href, forum|
    user = get_random_user(ARGV[0])
    article = get_random_content(ARGV[1])
    puts user, article
    post_article(forum, user, article)
    
  end

end
