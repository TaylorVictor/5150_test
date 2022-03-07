'''
@File    :  parser.py
@Author  :  Vector
@Date    :  2021/9/7--16:49
@Desc    :
@PARAMs  :
@RETURN  :
'''
import re
import traceback

import requests
from bs4 import BeautifulSoup

from table_extractor import tableExtractor

# mongo的连接
# mongo_uri = 'mongodb://127.0.0.1:27017'
# mongo_db = 'baike_db'
# collection_name = 'baike'
# client = pymongo.MongoClient(mongo_uri)
# db = client[mongo_db]
#
# # 读出urllist路径
# urlpath = 'D:/baikeinfo/urlGetted.txt'
# try:
#     with open(urlpath, 'r', encoding='utf-8-sig') as fp:
#         urlList = fp.read().split("\n")[:-1]
# except:
#     traceback.print_exc()
#
# #读出html页面的路径
# htmlpath = "D:/baike_html/"
#
# #存储图片的路径：
pic_path="D:/pic/"
# #线程数
# thread_num=16

# def worker(queue,name):
#     while True:
#         if queue.empty():
#             print(name+":队列为空！")
#         else:
#
#             url=queue.get()
#             if url:
#                 url_decode=htmlpath+urllib.parse.unquote(url).strip()
#                 filename=htmlpath+re.sub("[/?&=#.\"'\\:*<>\|]", "_", url_decode.split("/", 4)[-1])
#                 try:
#                     with codecs.open(filename + '.txt', "rb", encoding='utf-8-sig') as f:
#                     # 将这个文本对象转换为HTML即可
#                         html = HTML(html=f.read())
#                 except:
#                     traceback.print_exc()
#
#                 item=html_parse(html,url)
#                 try:
#                     db[collection_name].insert_one(ItemAdapter(item).asdict())
#                 except:
#                     traceback.print_exc()

# 定义解析函数
def html_parse(html, url):
    item = {}
    item['lemmaUrl'] = url
    item['lemmaTitle'] = html.find('h1')[0].text
    item['summary'] = summaryExtractor(html)
    item['basicInfo'] = basicInfoExtractor(html)
    item['introduction'] = introductionExtractor(html)
    item['tableList'] = tablesExtractor(html.html)
    item['pictureList'] = pictureExtractor(html)
    item['catalog'] = catalogExtractor(html)

    list = item['pictureList']
    for pic in list:
        try:
            with open(pic_path + pic.replace("https://bkimg.cdn.bcebos.com/pic/", '').split('?')[0] + '.png',
                      'wb') as fp:
                fp.write(requests.get(pic).content)
        except:
            traceback.print_exc()
    return item




def excludeDescriptionAndPrefix(element):
    if len(element.find('.description')) != 0 and len(element.find('.title-prefix')) != 0:
        strpara = str(element.text).replace(str(element.find('.description')[0].text), "", 1).replace(
            str(element.find('.title-prefix')[0].text), "", 1)
        return strpara
    elif len(element.find('.description')) != 0:
        return str(element.text).replace(str(element.find('.description')[0].text), "", 1)
    elif len(element.find('.title-prefix')) != 0:
        return str(element.text).replace(str(element.find('.title-prefix')[0].text), "", 1)
    else:
        return element.text

    # 简介提取器


def summaryExtractor(response):
    summarylist = response.find('.lemma-summary')
    # 将简介放入字典
    summary = ""
    for item in summarylist:
        if summary == "":
            summary += item.text
        else:
            summary = summary + '\n' + item.text
    return summary.replace('\xa0', '')

    # 目录提取器


def catalogExtractor(response):
    catalog = response.find(".catalog-list", first=True)
    catalogList = {}
    if catalog:
        # 只拿到第一个目录
        title_list = catalog.find('li')
        if len(title_list) != 0:
            # 一级目录
            titleLevel1 = '目录'
            catalogList[titleLevel1] = []
            titleLevel2 = []
            for title in title_list:
                # 如果这是一个一级目录
                if title.find('.level1', first=True):
                    # 如果二级目录不是空，那么放入一级目录，并更新当前一级目录和二级目录列表
                    if titleLevel2:
                        catalogList[titleLevel1] = titleLevel2
                    titleLevel1 = title.find('.level1', first=True).text.split(' ')[1]
                    catalogList[titleLevel1] = []
                    titleLevel2 = []
                    pass
                elif title.find('.level2', first=True):
                    titleLevel2.append(title.find('.level2', first=True).text.split(' ')[1])
                    pass
            catalogList[titleLevel1] = titleLevel2
            if not catalogList['目录']:
                catalogList.pop('目录')
            return catalogList
        else:
            return {}
    else:
        return {}
    # pass

    # 基本信息提取器


def basicInfoExtractor(response):
    list = response.find('.basic-info .basicInfo-block .basicInfo-item')
    dic = {}
    for i, item in enumerate(list, 0):
        if (i % 2 == 0):
            dic[item.text.replace('\xa0', '')] = list[i + 1].text

    for key in dic.keys():
        dic[key] = str(dic[key]).replace('展开', '').replace('收起', '').split('\n')
    return dic

    # 正文提取器


def introductionExtractor(response):
    info = {}
    paralist = response.find('.title-text,.para')
    index = -1
    paraLength = len(paralist)
    for i in range(0, paraLength):
        if 'title-text' in paralist[i].attrs['class']:
            index = i
            break
    # 如果index==-1，那么就说明没有标题
    if index == -1:
        info['introduction'] = ""
        for i in range(index, paraLength):
            info['introduction'] += paralist[i].text
    else:
        # 存在标题，把标题前面的段落剔除
        info['introduction'] = {}
        induction = ""
        # 这里申明一个正文作为一级标题，因为有些界面有二级标题但没有一级标题，队友有一级标题的页面，这个列表是空的
        headline = "正文"
        info['introduction'][headline] = []
        for i in range(index, paraLength):
            if paralist[i].find('h2', first=True):
                if excludeDescriptionAndPrefix(paralist[i]) not in info['introduction'].keys():
                    info['introduction'][excludeDescriptionAndPrefix(paralist[i])] = []
                if induction != "":
                    info['introduction'][headline].append(induction)
                # 更新一级标题
                headline = excludeDescriptionAndPrefix(paralist[i])
                induction = ""
            elif paralist[i].find('h3', first=True):
                if induction != "":
                    info['introduction'][headline].append(induction)
                induction = excludeDescriptionAndPrefix(paralist[i]) + ':\n\n'
            else:
                induction += excludeDescriptionAndPrefix(paralist[i])
        info['introduction'][headline].append(induction)
        if not info['introduction']['正文']:
            info['introduction'].pop('正文')
    return info['introduction']

    # 表格提取器，表格提取器的思想参考方案文档


def tablesExtractor(response):
    soup = BeautifulSoup(response, 'lxml')
    tableList = []
    tables = soup.select('table')
    for table in tables:
        tableList.append(tableExtractor(table).parse().return_dict())
    return tableList

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


def pictureExtractor(response):
    content = response.find('.body-wrapper', first=True)
    pictureList = content.find('img', first=False)
    pictureUrlList = []
    for picture in pictureList:
        # 如果有懒加载的data-src，那么就拿data-src，如果没有那么就拿src：
        if 'data-src' in picture.attrs.keys():
            if re.match('https://bkimg.cdn.bcebos.com/pic', picture.attrs['data-src']):
                pictureUrlList.append(picture.attrs['data-src'])
        elif re.match('https://bkimg.cdn.bcebos.com/pic', picture.attrs['src']):
            pictureUrlList.append(picture.attrs['src'])
    return pictureUrlList

    # 百科连接提取，提取目标元素中的连接


def baikeLinkExtractor1(element):
    links = element.links
    validLinks = []
    for link in links:
        validLinks.append("https://baike.baidu.com" + link)
    return validLinks






