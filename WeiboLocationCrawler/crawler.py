# coding:utf-8
# version:python3.7
# author:Ivy

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sqlite3, pandas
import random
import traceback
import threading


def weibotable():
    #cur.execute("DROP TABLE IF EXISTS weibo")
    create_weibotable='''CREATE TABLE weibo(Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    weibo_id TEXT UNIQUE,
                                    time TEXT,
                                    created_time TEXT,
                                    user_id TEXT,
                                    source TEXT,
                                    content TEXT,
                                    reposts_count INTEGER,
                                    comments_count INTEGER,
                                    attitudes_count INTEGER,
                                    pending_approval_count INTEGER,
                                    place TEXT)'''
    cur.execute(create_weibotable)
    conn.commit()



def pictable():
    #cur.execute("DROP TABLE IF EXISTS pic")
    create_pictable='''CREATE TABLE pic(Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    pid TEXT NOT NULL,
                                    img TEXT,
                                    img_large TEXT)'''
    cur.execute(create_pictable)
    conn.commit()



def picweibotable():
    #cur.execute("DROP TABLE IF EXISTS picweibo")
    create_picweibotable='''CREATE TABLE picweibo(pid TEXT,
                                    weibo_id TEXT,
                                    PRIMARY KEY (pid, weibo_id))'''
    cur.execute(create_picweibotable)
    conn.commit()



def db_init():
    weibotable()
    pictable()
    picweibotable()


# 随机选择一个代理
def random_ip(ippool):
    num = random.randint(0,len(ippool)-1) #随机选一个0到10的整数
    return ippool[num]

# 爬虫基本功能部分，返回网页的一个json
def get_tweets(URL,page,ippool):
    url=URL.format(str(page))

    while True:
        try:
            proxy_ip=random_ip(ippool)
            res = requests.get(url, proxies=proxy_ip)
            res.encoding='utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            jd = json.loads(res.text)
        except:
            print('代理有问题呀，换个ip试试')
            continue

        if (jd['ok']==0) and ("这里还没有内容" in str(jd)):
            print(jd)
            return 0

        if jd['ok']==0:
            print('获取地点的页面失败啊，换个ip试试')
        else:
            break

    # 第一页的结果会有点不一样
    if page == 1 :
        if jd['data']['cards'][0]['card_id']=='card_hq_poiweibo':
            tweets=jd['data']['cards'][0]['card_group']
        else:
            tweets=jd['data']['cards'][1]['card_group']
    else:
        tweets=jd['data']['cards'][0]['card_group']

    return tweets

def writedb(tweets,page):
    # 遍历每条微博
    for tweet in tweets:
        # 整理微博表的数据
        temp = [0 for i in range(11)]  # 初始化一行，一共有11列

        temp[0] = tweet['mblog']['id']
        temp[1] = current_time
        temp[2] = tweet['mblog']['created_at']
        temp[3] = tweet['mblog']['user']['id']
        temp[4] = tweet['mblog']['source']
        temp[5] = re.sub("[A-Za-z0-9\!\%\[\]\,\。\<\-\=\"\:\/\.\?\&\_\>\'\;\ ]", "", tweet['mblog']['text'])
        temp[6] = tweet['mblog']['reposts_count']
        temp[7] = tweet['mblog']['comments_count']
        temp[8] = tweet['mblog']['attitudes_count']
        temp[9] = tweet['mblog']['pending_approval_count']
        temp[10] = place

        # 不记录重复的微博
        temp_pd = pandas.read_sql_query("SELECT * FROM weibo",conn)
        all_id = temp_pd['weibo_id'].values
        if temp[0] in all_id:
            #print('这条微博爬过啦，跳过！')
            continue

        # 删掉来源里面那些乱七八糟的字符
        temp[4]=temp[4].replace("'","")
        temp[4]=temp[4].replace('"','')

        ins="INSERT INTO weibo VALUES (null,"+",".join(["'%s'" %x for x in temp])+")"
        cur.execute(ins)
        conn.commit()
        #print('Page',page,' %s 这条微博写进微博表啦'%temp[0])

        # 如果存在图片的话，就更新图片表和联立表
        if 'pics' in tweet['mblog'].keys():
            for img in tweet['mblog']['pics']:
                # 向图片和微博联立表中插入数据
                ins="INSERT INTO picweibo(pid, weibo_id) VALUES ('%s', '%s')"%(img['pid'], tweet['mblog']['id'])
                cur.execute(ins)
                conn.commit()

                # 整理图片表的数据
                temp_pic = [0 for i in range(3)]  # 初始化一行，一共有4列

                temp_pic[0] = img['pid']
                temp_pic[1] = img['url']
                temp_pic[2] = img['large']['url']

                # 向图片表中插入数据
                ins="INSERT INTO pic VALUES (null,"+",".join(["'%s'" %x for x in temp_pic])+")"
                cur.execute(ins)
                conn.commit()
            #print('Page',page,' %s 这条微博的图片也写进图片表啦'%temp[0])


def main(row,ippool,yag,emailname):

    global conn,cur,place,pid

    # 读取资料文档
    f=pandas.read_csv("pid.csv")
    place=f['pname'][row]
    pid=f['pid'][row]

    # 连接数据库
    conn = sqlite3.connect('weibo.sqlite',check_same_thread=False)
    cur = conn.cursor()

    # 初始化数据库，如果已经存在了就接着爬就好了
    try:
        db_init()
    except:
        pass

    # 微博位置URL
    URL = 'https://m.weibo.cn/api/container/getIndex?containerid='+pid+'_-_weibofeed&luicode=10000011&lfid=100103type%3D1%26q%3D%E6%AD%A6%E6%B1%89%E5%A4%A7%E5%AD%A6&page={}'

    print('******************开始爬%s的微博了*******************************'%place)
    try:
        time_start=time.time()

        # 爬150页微博
        page=1
        while True:
            print('开始爬',place,'第',page,'页')

            # 获取当前时间
            global current_time
            current_time = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
            # 获取一个页面的所有内容，json格式
            tweets = get_tweets(URL,page,ippool)

            #判断是不是到底了
            if "周边值得去" in str(tweets):
                print('爬到底了！')
                break

            if tweets==0:
                print('已经到第',page,'页了，没有内容了')
                break

            # 写入数据库
            writedb(tweets,page)


            print(place,' 第',page,'页爬完了！')
            page+=1

        time_end=time.time()
        print(place,' time cost ',time_end-time_start,'s')

        print('******************%s的微博爬完了*******************************'%place)


    except:
        e = traceback.format_exc()
        # 要是报错了，就发邮件然后退出
        print(e)
        yag.send(to = [emailname], subject = place+' Break!!!!!', contents = [e])

    finally:
        #关闭数据库
        cur.close()
        conn.close()


    print(place,'爬完了！等待下一次')
