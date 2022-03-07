import logging
import os
import re
import urllib.parse

import scrapy
import urllib3.util
from bs4 import BeautifulSoup
from scrapy import Item

from baikeCrawler.items import PictureItem

from baikeCrawler.items import BaikecrawlerItem
from scrapy.http import TextResponse

from baikeCrawler.spiders.table_extractor import tableExtractor
# request-html只是一个解析包，所有的请求都是可以相互转换的
from requests_html import HTML

# 移除词条的中的描述信息和前缀
from baikeCrawler.items import FileItem

from baikeCrawler.items import UrlItem


# def excludeDescriptionAndPrefix(element):
#     if len(element.find('.description')) != 0 and len(element.find('.title-prefix')) != 0:
#         strpara = str(element.text).replace(str(element.find('.description')[0].text), "", 1).replace(
#             str(element.find('.title-prefix')[0].text), "", 1)
#         return strpara
#     elif len(element.find('.description')) != 0:
#         return str(element.text).replace(str(element.find('.description')[0].text), "", 1)
#     elif len(element.find('.title-prefix')) != 0:
#         return str(element.text).replace(str(element.find('.title-prefix')[0].text), "", 1)
#     else:
#         return element.text
#
# #简介提取器
# def summaryExtractor(response):
#     summarylist = response.find('.lemma-summary')
#     # 将简介放入字典
#     summary = ""
#     for item in summarylist:
#         if summary == "":
#             summary += item.text
#         else:
#             summary = summary + '\n' + item.text
#     return summary.replace('\xa0', '')
#
# #目录提取器
# def catalogExtractor(response):
#     catalog = response.find(".catalog-list",first=True)
#     catalogList = {}
#     if catalog:
#         # 只拿到第一个目录
#         title_list = catalog.find('li')
#         if len(title_list) != 0:
#             # 一级目录
#             titleLevel1 = '目录'
#             catalogList[titleLevel1]=[]
#             titleLevel2 = []
#             for title in title_list:
#                 # 如果这是一个一级目录
#                 if title.find('.level1', first=True):
#                     # 如果二级目录不是空，那么放入一级目录，并更新当前一级目录和二级目录列表
#                     if titleLevel2:
#                         catalogList[titleLevel1] = titleLevel2
#                     titleLevel1 = title.find('.level1', first=True).text.split(' ')[1]
#                     catalogList[titleLevel1]=[]
#                     titleLevel2 = []
#                     pass
#                 elif title.find('.level2', first=True):
#                     titleLevel2.append(title.find('.level2', first=True).text.split(' ')[1])
#                     pass
#             catalogList[titleLevel1] = titleLevel2
#             if not catalogList['目录']:
#                 catalogList.pop('目录')
#             return catalogList
#         else:
#             return {}
#     else:
#         return {}
#     # pass
#
#
# # 基本信息提取器
# def basicInfoExtractor(response):
#     list = response.find('.basic-info .basicInfo-block .basicInfo-item')
#     dic = {}
#     for i, item in enumerate(list, 0):
#         if (i % 2 == 0):
#             dic[item.text.replace('\xa0', '')] = list[i + 1].text
#
#     for key in dic.keys():
#         dic[key] = str(dic[key]).replace('展开', '').replace('收起', '').split('\n')
#     return dic
#
#
# #正文提取器
# def introductionExtractor(response):
#     info={}
#     paralist = response.find('.title-text,.para')
#     index = -1
#     paraLength=len(paralist)
#     for i in range(0,paraLength):
#         if 'title-text' in paralist[i].attrs['class']:
#             index=i
#             break
#     # 如果index==-1，那么就说明没有标题
#     if index == -1:
#         info['introduction']=""
#         for i in range(index,paraLength):
#             info['introduction']+=paralist[i].text
#     else:
#         # 存在标题，把标题前面的段落剔除
#         info['introduction'] = {}
#         induction = ""
#         #这里申明一个正文作为一级标题，因为有些界面有二级标题但没有一级标题，队友有一级标题的页面，这个列表是空的
#         headline="正文"
#         info['introduction'][headline]=[]
#         for i in range(index,paraLength):
#             if paralist[i].find('h2', first=True):
#                 if excludeDescriptionAndPrefix(paralist[i]) not in info['introduction'].keys():
#                     info['introduction'][excludeDescriptionAndPrefix(paralist[i])] = []
#                 if induction != "":
#                     info['introduction'][headline].append(induction)
#                 # 更新一级标题
#                 headline = excludeDescriptionAndPrefix(paralist[i])
#                 induction = ""
#             elif paralist[i].find('h3', first=True):
#                 if induction != "":
#                     info['introduction'][headline].append(induction)
#                 induction = excludeDescriptionAndPrefix(paralist[i]) + ':\n\n'
#             else:
#                 induction += excludeDescriptionAndPrefix(paralist[i])
#         info['introduction'][headline].append(induction)
#         if not info['introduction']['正文']:
#             info['introduction'].pop('正文')
#     return info['introduction']
#
#
# # 表格提取器，表格提取器的思想参考方案文档
# def tablesExtractor(response):
#     soup = BeautifulSoup(response, 'lxml')
#     tableList = []
#     tables = soup.select('table')
#     for table in tables:
#         tableList.append(tableExtractor(table).parse().return_dict())
#     return tableList


# 百科连接提取
def baikeLinksExtractor(response):
    content = response.find('.body-wrapper')[0]
    links = []
    if content:
        links = content.links
    # 提取有效的连接
    validLinks = []
    for link in links:
        if re.match('/item/', link):
            validLinks.append("https://baike.baidu.com" + link)
    return validLinks


# 图片提取
# def pictureExtractor(response):
#     content = response.find('.body-wrapper', first=True)
#     pictureList = content.find('img', first=False)
#     pictureUrlList = []
#     for picture in pictureList:
#         #如果有懒加载的data-src，那么就拿data-src，如果没有那么就拿src：
#         if 'data-src' in picture.attrs.keys():
#             if re.match('https://bkimg.cdn.bcebos.com/pic', picture.attrs['data-src']):
#                 pictureUrlList.append(picture.attrs['data-src'])
#         elif re.match('https://bkimg.cdn.bcebos.com/pic', picture.attrs['src']):
#             pictureUrlList.append(picture.attrs['src'])
#     return pictureUrlList

# 百科连接提取，提取目标元素中的连接
def baikeLinkExtractor1(element):
    links = element.links
    validLinks = []
    for link in links:
        validLinks.append("https://baike.baidu.com" + link)
    return validLinks


class BaikespiderSpider(scrapy.Spider):
    name = 'baikeSpider'  # 爬虫名
    # 这里就必须是这个域，如果不是这个因为可能是baike.baidu.com/view  或者baike.baidu.com/item
    allowed_domains = ['baike.baidu.com']  # 允许爬取的范围

    startPage = 1  # view的起始页(每次抓取都需要修改）
    endPage = 100  # view的终止页（每次抓取需要修改）
    start_urls = []  # 最开始的url地址（不需要修改）
    urlPattern = 'https://baike.baidu.com/view/{0}.htm'  # 定义爬取的url格式（不需要修改)
    urlGettedFile = "D:/baikeinfo/urlGetted.txt"  # 定义已经爬取的文url的文件路径（需要自己创建文件夹）
    urlErrorFile = "D:/baikeinfo/urlError.txt"  # 定义爬取失败的url的路径（需要自己创建文件夹与文件）
    savePath = "D:/baike_html/"  # 定义存储路径（需要自己创建文件夹）

    urlGettedSet = set()

    def __init__(self):
        # 爬虫初始化的时候需要加载好已经爬取的集合和
        for i in range(self.startPage, self.endPage):
            self.start_urls.append(self.urlPattern.format(i))

        # 读入已经爬过的url
        try:
            with open(self.urlGettedFile, 'r', encoding='utf-8-sig') as fp:
                urlGettedList = fp.read().split("\n")[:-1]
                self.urlGettedSet = set(urlGettedList)
        except:
            print("Read GettedList Error")
        # 上次迭代的错误页面（超时等），并将这些页面加入初始要爬的页面的start_urls中
        urlErrorList = []
        try:
            with open(self.urlErrorFile, 'r', encoding='utf-8-sig') as fp:
                urlErrorList = fp.read().split("\n")[:-1]
            # 清空文件内容
            with open(self.urlErrorFile, 'w', encoding='utf-8-sig') as fp:
                fp.write('')
        except:
            print("Read ErrorList Error！")
        # 将上次错误的页面列表加入初始的url队列
        for url in urlErrorList:
            self.start_urls.append(url)

    def parse(self, response):

        # url编码
        url = urllib.parse.unquote(response.url).strip()

        if str(response.url).find("error.html") != -1:  # 如果当前页面是空那么直接返回即可
            return
        # 因为是按照view遍历，而返回的是item，所以需要先判断是不是在已经存储的url里面防止重复写入，如果已经抓取过，直接返回
        if response.url in self.urlGettedSet:
            return

        html = HTML(html=response.text)  # 将返回的response转换为request-html能解析的方式
        list1 = html.find('.lemmaWgt-subLemmaListTitle')
        # polysemantList = html.find('.polysemantList-wrapper,cmn-clearfix', first=True)
        # 如果只是有多义词列表
        if list1:
            lemmaWgtElement = html.find(".custom_dot,para-list,list-paddingleft-1", first=True)
            urlList = baikeLinkExtractor1(lemmaWgtElement)  # 获取同义词连接
            for link in urlList:
                if link not in self.urlGettedSet:
                    req = scrapy.http.request.Request(link, callback=self.parse)
                    yield req
        else:
            # 如果有同义词连接，那么就提取所有百科连接进行
            print(response)
            urlList = baikeLinksExtractor(html)
            for link in urlList:
                # 从网页中拿到的连接是item所以不再需要判断
                if link not in self.urlGettedSet:
                    req = scrapy.http.request.Request(link, callback=self.parse)
                    yield req
                    # 1、需要将当前页面的url和html页面给写入文件
            filename = re.sub("[/?&=#.\"'\\:*<>\|]", "_", url.split("/", 4)[-1])  # 将url中的特殊字符给替换为下划线
            fitem = FileItem()
            # 当前程序访问过的url还需要加入已经访问的set吗，实际不需要，因为在一次运行中,不会重复解析，但需要写入文件夹方便下次读出这个
            fitem['Name'] = filename + ".txt"
            fitem['Content'] = str(html.html)
            # print(str(html.text))
            yield fitem

            urlItem = UrlItem()
            urlItem['url'] = response.url
            yield urlItem

    # 这个是解析的函数
    # def extract_info(self,response):
    #     print(response.url)
    #     #如果返回的没有多义词且有内容，那么就直接解析并获取链接，如果当前view没有信息，那么就直接返回
    #     #如果当前view有只含有同义词，那么先获取同义词链接然后，然后对同义词链接进行请求
    #     #如果包含同义词和详细页面，也先遍历同义词页面进行请求，然后所有的请求都返回回来后再解析当前页面，然后就可以解析所有的页面了
    #     # 这里先解析成request能解析的形式
    #     #记录当前返回的view号
    #     #logging.warning("当前返回结果的view号："+str(response.meta['id']))
    #     html = HTML(html=response.text)
    #     list1 = html.find('.lemmaWgt-subLemmaListTitle')
    #     polysemantList = html.find('.polysemantList-wrapper,cmn-clearfix',first=True)
    #     if str(response.url).find("error.html") != -1:
    #         #如果当前页面是空那么直接返回即可
    #         return
    #     #如果当前页面是验证码，那么记录当前的view号
    #     elif str(response.url).find("wappass") != -1:
    #         with open("viewid.txt",'a+') as fp:
    #             fp.write(str(response.meta['id'])+'\n')
    #         return
    #     elif list1:
    #         #拿到多义词表进行遍历
    #         lemmaWgtElement=html.find(".custom_dot,para-list,list-paddingleft-1",first=True)
    #         urlList=baikeLinkExtractor1(lemmaWgtElement)
    #         for link in urlList:
    #             req=scrapy.http.request.Request(link,callback=self.extract_info)
    #             req.meta['id']=response.meta['id']
    #             yield req
    #
    #     #如果当前页面含有多义词，而且含有详细信息
    #     elif polysemantList:
    #         linkList=baikeLinkExtractor1(polysemantList)
    #         for link in linkList:
    #             req=scrapy.http.request.Request(link,callback=self.extract_info)
    #             req.meta['id'] = response.meta['id']
    #             yield req
    #         #递归回来获取详细信息
    #         item = BaikecrawlerItem()
    #         item['lemmaUrl'] = response.url
    #         item['lemmaTitle'] = html.find('h1')[0].text
    #         item['summary'] = summaryExtractor(html)
    #         item['basicInfo'] = basicInfoExtractor(html)
    #         item['introduction'] = introductionExtractor(html)
    #         item['tableList'] = tablesExtractor(response.text)
    #         item['pictureList'] = pictureExtractor(html)
    #         item['catalog']=catalogExtractor(html)
    #         yield item
    #         # 获取图片
    #         picItem = PictureItem()
    #         picItem['pictureList'] = item['pictureList']
    #         yield picItem
    #     else:
    #         # 获取信息
    #         item = BaikecrawlerItem()
    #         item['lemmaUrl'] = response.url
    #         item['lemmaTitle'] = html.find('h1')[0].text
    #         item['summary'] = summaryExtractor(html)
    #         item['basicInfo'] = basicInfoExtractor(html)
    #         item['introduction'] = introductionExtractor(html)
    #         item['tableList'] = tablesExtractor(response.text)
    #         item['pictureList'] = pictureExtractor(html)
    #         item['catalog'] = catalogExtractor(html)
    #         yield item
    #         # 获取图片
    #         picItem = PictureItem()
    #         picItem['pictureList'] = item['pictureList']
    #         yield picItem
