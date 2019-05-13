# coding:utf-8
# version:python 3.7
# author:Ivy

import sqlite3
import requests,json
import re,random,time

# 就是同文件夹的ippool.py
import buildippool

def repostTable():
    createRepostTable='''CREATE TABLE IF NOT EXISTS  repost(Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    mid TEXT UNIQUE,
                                    uid TEXT,
                                    user TEXT,
                                    content TEXT,
                                    time TEXT,
                                    root_mid TEXT)'''
    cur.execute(createRepostTable)
    conn.commit()

def commentTable():
    createCommentTable='''CREATE TABLE IF NOT EXISTS  comment(Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                    cid TEXT UNIQUE,
                                    uid TEXT,
                                    user TEXT,
                                    content TEXT,
                                    time TEXT,
                                    root_mid TEXT)'''
    cur.execute(createCommentTable)
    conn.commit()

def dbInit(type):
    if type=='repost':
        repostTable()
    else:
        commentTable()

def getJson(mid,page,type,ippool):
    global cookie

    if type=='repost':
        url='https://m.weibo.cn/api/statuses/repostTimeline?id={}&page={}'.format(mid,page)
    else:
        url='https://m.weibo.cn/api/comments/show?id={}&page={}'.format(mid,page)
    headers = {
    'User-agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    'Host' : 'm.weibo.cn',
    'Accept' : 'application/json, text/plain, */*',
    'Accept-Language' : 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding' : 'gzip, deflate, br',
    'Referer' : 'https://m.weibo.cn/status/' + mid,
    'DNT' : '1',
    'Connection' : 'keep-alive',
    }

    proxy_ip=ippool[random.randint(0,len(ippool)-1)]
    while True:
        try:
            res=requests.get(url=url,headers=headers, proxies=proxy_ip,timeout=20)
            res.encoding='utf-8'
            if res.status_code==404:
                if 'cookie' in headers.keys():
                    cookie=input('cookie失效了，重新输入下：')
                headers['cookie']=cookie
                time.sleep(3)
                continue
            break
        except requests.exceptions.ProxyError as e:
            # 如果是代理不行的话
            print('代理不行，换代理')
            ippool.remove(proxy_ip)
            # 代理池没有存货了的话，那就再爬一遍代理
            if len(ippool)<1:
                ippool=ippool.buildippool()
            proxy_ip=ippool[random.randint(0,len(ippool)-1)]
        except Exception as e:
            # 其他错误的话，就打印看下，退出程序
            # 但是好像一般没有
            print(e)
            sys.exit()

    jd = json.loads(res.text)

    if jd['ok']==1:
        return jd,ippool
    else:
        print(jd) # 也可以不打印这个，但是有点怕是其他的报错情况让ok为0
        print('这里好像没内容了')
        return 0,ippool

def crawlRepocomm(ippool,mid,type):
    page=1
    while True:
        print('准备开始爬第',page,'页的'+type)
        jd,ippool=getJson(mid,page,type,ippool)
        if jd==0:
            print('转发爬完了')
            break
        if type=='repost':
            WriteRepo(jd,mid)
        else:
            WriteComm(jd,mid)
        page+=1

    return ippool

def WriteRepo(jd,mid):
    data=jd['data']['data']
    for tweet in data:
        text=re.sub('[\'\"]','',tweet['text'])
        ins="INSERT OR IGNORE INTO repost(mid, uid,user,content,time,root_mid) VALUES ('{}','{}','{}','{}','{}','{}')".format(tweet['mid'],tweet['user']['id'],tweet['user']['screen_name'],text,tweet['created_at'],mid)
        cur.execute(ins)
        conn.commit()

def WriteComm(jd,mid):
    data=jd['data']['data']
    for tweet in data:
        text=re.sub('[\'\"]','',tweet['text'])
        ins="INSERT OR IGNORE INTO comment(cid, uid,user,content,time,root_mid) VALUES ('{}','{}','{}','{}','{}','{}')".format(tweet['id'],tweet['user']['id'],tweet['user']['screen_name'],text,tweet['created_at'],mid)
        cur.execute(ins)
        conn.commit()

def main(mid,type,cookie_main):

    if (type !='repost') and (type != 'comment'):
        return 0

    global conn,cur,cookie

    cookie=cookie_main

    # 连接数据库
    conn = sqlite3.connect('weibo.sqlite',check_same_thread=False)
    cur = conn.cursor()

    # 初始化数据库，如果已经存在了就接着爬就好了
    dbInit(type)
    print('数据库已准备')

    # 建立代理池
    ippool=buildippool.buildippool()

    crawlRepocomm(ippool,mid,type)

    # 关闭数据库
    cur.close()
    conn.close()

    return 1
