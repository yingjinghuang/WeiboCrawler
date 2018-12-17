# coding:utf-8
# version:python3.7
# author:Ivy

import crawler
import buildip
import time
import yagmail
import pandas
import sqlite3

if __name__ == '__main__':
    ########################### 自己设置区 ###############################
    emailname=None
    emailpassword=None
    #####################################################################

    # 登录你的邮箱
    yag = yagmail.SMTP(user = emailname, password = emailpassword, host = 'smtp.qq.com')

    # 位置个数
    temp_pd = pandas.read_csv("pid.csv")
    n=temp_pd.shape[0]

    while True:

        time_start=time.time()

        # 建立代理池
        ippool=buildip.buildippool()
        #ippool=[{}] # 测试专用行

        print('*************************开始爬取%s个地点的微博*********************'%str(n))
        #建立进程
        for i in range(n):
            crawler.main(i,ippool,yag,emailname)

        time_end=time.time()
        print(' time cost ',time_end-time_start,'s')

        print('***********************休息三小时再继续爬********************')
        conn=sqlite3.connect('weibo.sqlite')
        weibo_pd = pandas.read_sql_query("SELECT * FROM weibo",conn)
        wb_detail=weibo_pd['place'].value_counts().to_dict()
        wb_m = weibo_pd.shape[0]
        pic_pd = pandas.read_sql_query("SELECT * FROM pic",conn)
        pic_m = pic_pd.shape[0]
        conn.close()
        yag.send(to = [emailname], subject = 'All Done', contents = ['这一段时间的都爬完了，三个小时后继续。耗时{}秒。现在共有微博{}条，图片{}张。具体微博情况为{}'.format(time_end-time_start, wb_m, pic_m,wb_detail)])
        time.sleep(10800) #设置3个小时执行一次
