# coding:utf-8
# version:python3.7
# author:Ivy

import sqlite3
import os
import pandas
import numpy
import time
import yagmail
import requests,re
from bs4 import BeautifulSoup

############################ 自主设置区 #################################

# 邮箱信息
emailname=None
emailpassword=None
# 数据库路径
weibo_db='weibo.sqlite'
user_db='user.sqlite'

##########################################################################

# 登录邮箱
yag = yagmail.SMTP(user = emailname, password = emailpassword, host = 'smtp.qq.com')
# 连接数据库
conn = sqlite3.connect(user_db)
cur = conn.cursor()

# 创建用户表
def usertable():
    create_usertable='''CREATE TABLE user(Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    user_id TEXT UNIQUE,
                                    nickname TEXT,
                                    gender TEXT ,
                                    location TEXT,
                                    birthday TEXT,
                                    weibo_count INTEGER,
                                    follow_count INTEGER,
                                    followers_count INTEGER,
                                    description TEXT)'''
    cur.execute(create_usertable)
    conn.commit()



# 写用户表
def writeut(uid,cur,conn,cookies):

    # 先爬个人主页
    res1=requests.get('https://weibo.cn/'+uid,cookies=cookies,timeout=100)

    if '头像' not in res1.text:
        print('个人主页登录失败，换下cookie')
        return False
    print('成功登录用户个人主页')
    soup1 = BeautifulSoup(res1.text, "html.parser")
    weibotext = soup1.findAll("span",{"class":"tc"})[0].get_text()
    followtext = soup1.findAll("a",{"href":"/%s/follow"%uid})[0].get_text()
    fanstext = soup1.findAll("a",{"href":"/%s/fans"%uid})[0].get_text()
    weibo_count=int(weibotext[3:-1])
    follow_count=int(followtext[3:-1])
    fans_count=int(fanstext[3:-1])
    print('用户个人主页爬完了')

    # 再爬个人资料页
    res2=requests.get('https://weibo.cn/'+uid+'/info',cookies=cookies,timeout=100)
    if '昵称' not in res2.text:
        print('个人资料页登录失败，换下cookie')
        return False
    print('成功登录用户个人资料页')
    soup2 = BeautifulSoup(res2.text, "html.parser")
    info = soup2.findAll("div",{"class":"c"})[3].get_text()

    temp = [0 for i in range(9)]  # 初始化一行，一共有10列

    nickname=re.findall('昵称(.+?):',info)[0][1:-2]
    taglist=['性别','地区','生日','简介']
    for i in range(2,6):
        if taglist[i-2] not in info:
            if i<5:
                temp[i]='未知'
            else:
                temp[8]='未知' # 简介在第8列
        else:
            text=re.findall(taglist[i-2]+'(.+?):',info)
            # 有可能会匹配不到，是因为可能这是info里面的最后一个标签，后面就没有冒号可以匹配了，所以再匹配一次
            if len(text)<1:
                text=re.findall(taglist[i-2]+'(.+?)',info)
            text=text[0][1:]
            if text[-2:] == '取向':
                text=text[:-3]
            else:
                text=text[:-2]
            if i<5:
                temp[i]=text
            else:
                temp[8]=text # 简介在第8列
    temp[0]=uid
    temp[1]=nickname
    temp[5]=weibo_count
    temp[6]=follow_count
    temp[7]=fans_count

    # 删掉简介里面那些乱七八糟的字符
    temp[8]=temp[8].replace("'","")
    temp[8]=temp[8].replace('"','')

    ins="INSERT INTO user VALUES (null,"+",".join(["'%s'" %x for x in temp])+")"
    cur.execute(ins)
    conn.commit()
    print('用户 %s 已添加'%temp[1])
    return True


def getcookies():
    # 连接cookie池
    with open('cookie.txt','r') as f:
        cookie=f.read()
    cookies = {}
    for line in cookie.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name]=value
    return cookies


def main():
    # 初始化用户表，已经有了的话就继续写
    try:
        usertable()
        all_id = []
    except:
        temp_pd = pandas.read_sql_query("SELECT * FROM user",conn)
        all_id = list(temp_pd['user_id'].values)


    # 获取所有的用户id
    conn_w=sqlite3.connect(weibo_db)
    temp_pd = pandas.read_sql_query("SELECT * FROM weibo",conn_w)
    uid = list(temp_pd['user_id'].values)
    # unique一下，减少记录量
    uid=numpy.unique(uid)
    # 取两个列表的差集，得到uid中有all_id中没有的
    uid=list(set(uid).difference(set(all_id)))

    # 获取cookie
    cookies=getcookies()

    print('****************准备爬取',len(uid),'个用户信息*********************')
    for i in range(len(uid)):
        en=0 # 爬取失败次数
        u=uid[i]
        # 每10个用户休息一下
        if (i != 0) and (i%10==0):
            print('慢一点，停10s')
            time.sleep(10)

        while True:
            print('正在爬取第',i,'个用户')
            try:
                flag = writeut(u,cur,conn,cookies)
            except:
                print('请求超时错误了')
                en+=1
                if en==10:
                    print('需要更换cookies了')
                    yag.send(to = [emailname], subject = 'userinfo代码要换cookie了！！', contents = ['Check it!休息20分钟先'])
                    time.sleep(1200)
                    print('更换完毕，继续')
                    cookies=getcookies()
                    en=0

            if flag == True:
                break
            else:
                print('主机没响应什么的，错误了')
                en+=1
                if en==10:
                    print('需要更换cookies了')
                    yag.send(to = [emailname], subject = 'userinfo代码要换cookie了！！', contents = ['Check it!'])
                    t=input('更换完毕，则按回车继续：')
                    cookies=getcookies()
                    en=0

if __name__ == '__main__':
    while True:
        main()

        print('这段时间的用户信息爬取完毕')
        yag.send(to = [emailname], subject = '这段时间的用户信息爬取完毕', contents = ['三小时后再继续'])
        time.sleep(10800)
