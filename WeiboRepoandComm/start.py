# coding:utf-8
# version:python 3.7
# author:Ivy

import crawler


############## 自主设置区 #############################
cookie='' # 你自己的cookie
mid='' # 需要爬取的微博id
type='' # repost还是comment
######################################################

result=crawler.main(mid,type,cookie)
if result==0:
    print('type输入错了，修改后重新运行！')
else:
    print('爬完了')
