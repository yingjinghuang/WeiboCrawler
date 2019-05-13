# coding:utf-8
# version:python3.7
# author:Ivy

import requests,json
import random

# 爬取代理网站上可以用的代理，建立代理池
class Proxies:
    def __init__(self):
        self.proxy_list = []

    # 爬取西刺代理的国内高匿代理
    def get_proxy_nn(self):
        proxy_list = []
        res = requests.get("https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list")
        proxyList=str(res.text).split('\n')
        random.shuffle(proxyList)
        for i in range(100):
            proxy=proxyList[i]
            if '{' not in proxy:
                continue
            jd=json.loads(proxy)
            if jd['type']=='http':
                continue
            host_port=str(jd['host'])+':'+str(jd['port'])
            proxy_list.append(host_port)
            #rint(host_port,'Success')
        return proxy_list

    # 验证代理是否能用
    def verify_proxy(self, proxy_list):
        for proxy in proxy_list:
            proxies = {
                "https": proxy
            }
            try:
                if requests.get('https://www.baidu.com', proxies=proxies, timeout=5).status_code == 200:
                    if proxy not in self.proxy_list:
                        self.proxy_list.append(proxy)
                    print('Success',proxy)
            except:
                print('Fail',proxy)

    # 保存到ippool这个List里
    def save_proxy(self):
        ippool=[]
        print("开始存入代理池...")
        # 把可用的代理添加到代理池中
        for proxy in self.proxy_list:
            proxies={"http":proxy}
            ippool.append(proxies)
        return ippool


# 使用上面的类建立代理池
def buildippool():
    p = Proxies()
    results = p.get_proxy_nn()
    print("爬取到的代理数量", len(results))
    print("开始验证：")
    p.verify_proxy(results)
    print("验证完毕：")
    print("可用代理数量：", len(p.proxy_list))
    ippool = p.save_proxy()
    return ippool
