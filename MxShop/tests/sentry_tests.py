# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/4/15 0015 11:20'

# Sentry测试：使用python测试
# 1、导入包：pip install raven --upgrade

from raven import Client

dsn = ""  # Sentry的dsn

client = Client(dsn)
try:
    pass
except ZeroDivisionError:
    # 发送异常给Sentry
    client.captureException()


