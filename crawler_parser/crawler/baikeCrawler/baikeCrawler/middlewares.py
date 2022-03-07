# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import random
import time

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
    ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError
from twisted.web.client import ResponseFailed

from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.utils.response import response_status_message
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.utils.python import global_object_name
from baikeCrawler.util import Util


class BaikecrawlerSpiderMiddleware:


    @classmethod
    def from_crawler(cls, crawler):

        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):

        return None

    def process_spider_output(self, response, result, spider):

        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class BaikecrawlerDownloaderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

#设置随机uer-agent中间件
class RandomUserAgent(object):
    def __init__(self, agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('USER_AGENTS'))

    def process_request(self, request, spider):
        request.headers.setdefault('User-Agent', random.choice(self.agents))


class BaikeRetryMiddleware:
    #源码中将这些状态值定义为重新发送请求的状态值
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self, settings):
        if not settings.getbool('RETRY_ENABLED'):
            raise NotConfigured
        self.errorpath=settings.get('HTML_ERROR_PATH')
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if (
                isinstance(exception, self.EXCEPTIONS_TO_RETRY)
                and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            logger.info("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value(f'retry/reason_count/{reason}')
            return retryreq
        else:
            stats.inc_value('retry/max_reached')
            logger.error("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})

            #放弃超时的url并记录下来
            with open(self.errorpath,'a+') as fp:
                fp.write(str(request.url)+"\n")
#util = Util()  # 代理池



# 设置代理的中间件
#每一个中间件都有一个处理请求的函数和处理响应的函数
class ProxyMiddleware(object):

    #ip代理在处理请求时加入代理ip
    def process_request(self, request, spider):
        proxy = random.choice(util.proxies)
        request.meta['proxy'] = "http://"+proxy  # 重新请求

    #处理响应
    def process_response(self, request, response, spider):
        if response.status in [400, 403, 404, 407, 408, 429, 500, 501, 502, 503, 504, 509]:
            raise IgnoreRequest
        return response




#日志
logger = logging.getLogger(__name__)


class UpdateProxyMiddleware(object):
    # IOError is raised by the HttpCompression middleware when trying to
    # decompress an empty response
    #当出现这些问题时，就是重复请求的时候
    #python元组
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self, settings):
        if not settings.getbool('RETRY_ENABLED'):
            raise NotConfigured
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        _proxy = request.meta['proxy'].split('/')[2]  # 删除无效代理
        # proxy={
        #     'ip':_proxy.split(':')[0],
        #     'port':_proxy.split(':')[1]
        # }
        # logging.info('Removing failed proxy {0}'.format(proxy))
        try:
            util.proxies.remove(_proxy)
        except:
            pass
        while len(util.proxies) < util.poolsize:
            batch = util.get_proxy_list()
            util.proxies += batch

        logging.info('Proxy Pools:' + str(len(util.proxies)))  # 代理池大小

        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            proxy = random.choice(util.proxies)
            #print(proxy)
            request.meta['proxy'] = "http://"+proxy  # 重新请求
            return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            stats.inc_value('retry/max_reached')
            logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})