# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BaikecrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 定义百科文本数据存储的模板
    lemmaTitle=scrapy.Field()       #词条名称
    lemmaUrl=scrapy.Field()         #词条url，唯一
    summary=scrapy.Field()          #简介
    basicInfo=scrapy.Field()        #基本信息表（可能为空）
    introduction=scrapy.Field()     #详细介绍
    catalog=scrapy.Field()          #目录（可能为空）
    tableList=scrapy.Field()        #表格表（可能为空）
    pictureList=scrapy.Field()      #图片的url的列表
    #pass


class PictureItem(scrapy.Item):
    pictureList=scrapy.Field()      #存放图片的url
    #这里只拿到图片的url，爬取的工作交给pipelines
    #pass

#这里只存储成功返回的url
class UrlItem(scrapy.Item):
    url=scrapy.Field()

#定义文件的存储
class FileItem(scrapy.Item):
    #定义文件的存储名
    Name=scrapy.Field()
    #定义文件存储内容
    Content = scrapy.Field()