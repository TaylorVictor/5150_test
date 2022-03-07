import codecs
import logging
import traceback

import requests
from itemadapter import ItemAdapter
import pymongo

from baikeCrawler.items import BaikecrawlerItem, PictureItem

from baikeCrawler.items import FileItem, UrlItem


class BaikecrawlerPipeline:
    collection_name = 'baike'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        #只有当前实例是个百度百科信息的实例那么就将数据写入mongdb，如果不是那就放入其他的图片的pipeline
        if isinstance(item,BaikecrawlerItem):
            try:
                self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
            except:
                traceback.print_exc()
        return item

#距离引擎越近的pipeline会越先调用，而且上一个pipeline需要返回item才行

#百科图片的pipeline
class BaikePicturePipeline:
    def __init__(self, filepath):
        self.filepath =filepath

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            filepath=crawler.settings.get('PICPATH'),
        )

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        # 只有当前实例是个百度百科信息的实例那么就将数据写入mongdb，如果不是那就放入其他的图片的pipeline
        if isinstance(item, PictureItem):
            #print(PictureItem)
            list=item['pictureList']
            for pic in list:
                try:
                    with open(self.filepath+pic.replace("https://bkimg.cdn.bcebos.com/pic/",'').split('?')[0]+'.png','wb') as fp:
                        fp.write(requests.get(pic).content)
                except:
                    traceback.print_exc()
            return item
        else:
            # logging.info('Unkonwn Item')
            return item


class BaikeHtmlSavePipeline:

    def __init__(self, htmlpath):
        self.filepath = htmlpath
        self.fp=open("D:/baikeinfo/urlGetted.txt",'a+',encoding='utf-8-sig')
        print(self.filepath)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            htmlpath=crawler.settings.get('HTMLPATH'),
        )
    def process_item(self, item, spider):
        #如果当前的item是个文件的实例，那么就写入对应的写入文件
        if isinstance(item, FileItem):
            Place =item['Name']
            Content=item['Content']
            try:
                #写入文件
                with codecs.open(str(self.filepath)+str(Place),'wb',encoding="utf-8-sig") as fp:
                    fp.write(str(Content))
            except:
                    traceback.print_exc()
            return item
        elif isinstance(item,UrlItem):
            url=item['url']
            try:
                self.fp.write(url+"\n")
            except:
                logging.info("write error: "+str(url))
            return item
        else:
            logging.info('Unkonwn Item')
            return item