'''
@File    :  util.py
@Author  :  Vector
@Date    :  2021/8/27--18:12
@Desc    :
@PARAMs  :
@RETURN  :
'''
import logging
import time

import requests


class Util:
    def __init__(self):
        super(Util, self).__init__()
        self.poolsize=10
        self.proxies=[]
        while len(self.proxies)<self.poolsize:
            self.proxies=self.get_proxy_list()
    @staticmethod
    def get_proxy_list(num=30):
        api_url='http://vector.v4.dailiyun.com/query.txt?key=NP0DF2CC09&word=&count=20&rand=false&ltime=0&norepeat=false&detail=false'
        logging.warning("提取ip")
        iplist=requests.get(api_url).text.split('\r\n')[0:20]
        #这里通过代理公司提供的api进行获取代理ip
        return iplist
