'''
@File    :  main.py
@Author  :  Vector
@Date    :  2021/9/8--13:40
@Desc    :
@PARAMs  :
@RETURN  :
'''
import os
import queue
# mongo的连接
import codecs
import re
import threading
import traceback
import urllib

import pymongo
from itemadapter import ItemAdapter
from requests_html import HTML

from html_parser import html_parse

#mongodb的地址和数据库
mongo_uri = 'mongodb://127.0.0.1:27017'
mongo_db = 'baike_db'
collection_name = 'baike'
client = pymongo.MongoClient(mongo_uri)
db = client[mongo_db]

# 读出urllist路径
urlpath = 'D:/baikeinfo/urlGetted.txt'
try:
    with open(urlpath, 'r', encoding='utf-8-sig') as fp:
        urlList = fp.read().split("\n")[:-1]
except:
    traceback.print_exc()
#读出html页面的路径
htmlpath = "D:/baike_html/"
#出错的url存储下来
errorpath="D:/baikeinfo/urlError.txt"
#存储图片的路径：
pic_path="D:/pic/"
#线程数
thread_num=16
#全局队列
queue = queue.Queue()

def worker( name):
    while True:
        #如果队列为空
        if queue.empty():
            print(name + ":队列为空！")
            return

        else:
            url = queue.get()

            if url:
                url_decode = urllib.parse.unquote(url).strip()
                #如果当前url已经写入mongo，那么不用再解析
                #print(url)
                try:
                    if db[collection_name].find_one({"lemmaUrl": url}):
                        print("该{}已经被解析".format(url))
                        #print(db[collection_name].find({"lemmaUrl": url}))
                        # for doc in db[collection_name].find({"lemmaUrl": url}):
                        #     print(doc)
                        continue
                except:
                    traceback.print_exc()
                #html=HTML()
                print(name+"解析{}".format(url_decode))
                filename = htmlpath + re.sub("[/?&=#.\"'\\:*<>\|]", "_", url_decode.split("/", 4)[-1])
                #读出对应的html文件并进行解析，如果没有对应文件，那么说明，该url下的文件并没有保存下来，那么需要重新爬取
                try:
                    with codecs.open(filename + '.txt', "rb", encoding='utf-8-sig') as f:
                        # 将这个文本对象转换为HTML即可
                        html = HTML(html=f.read())
                except:

                    #如果没有找到该文件，应当将该url写入urlError.txt,下一次抓取网页的时候加入
                    try:
                        with open(errorpath, 'a+') as fp:
                            fp.write(url + "\n")
                    except:
                        traceback.print_exc()
                    traceback.print_exc()
                    continue

                item = html_parse(html, url)

                #写入队列
                db[collection_name].insert_one(ItemAdapter(item).asdict())



if __name__=="__main__":



    try:
        with open(urlpath, 'r', encoding='utf-8-sig') as fp:
            urlGettedList = fp.read().split("\n")[:-1]
        print("Read GettedList Success!")
    except:
        print("Read GettedList Error!")

    for url in urlGettedList:
        queue.put(url)
    print("url队列长度：{}".format(queue.qsize()))

    threads=[]
    for i in range(1,thread_num+1):
        name="线程{}".format(i)
        t=threading.Thread(target=worker,args=(name,))
        threads.append(t)
        t.start()


    #释放
    for i in range(thread_num):
        threads[i].join()
    #
    print("html页面解析完成！")
