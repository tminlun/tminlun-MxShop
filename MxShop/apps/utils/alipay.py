# pip install pycryptodome
__author__ = '田敏伦'

import json
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import b64encode, b64decode
from urllib.parse import quote_plus
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from base64 import decodebytes, encodebytes


class AliPay(object):
    """
    支付宝支付接口
    逻辑：
    初始化数据（app_notify_url、app_private_key、alipay_public_key、return_url、）
     --
    """
    def __init__(self, appid, app_notify_url, app_private_key_path,
                 alipay_public_key_path, return_url, debug=False):
        ''' 初始化数据 '''
        self.appid = appid
        self.app_notify_url = app_notify_url
        self.app_private_key_path = app_private_key_path  # 获取私钥的文件
        self.app_private_key = None  # 私钥
        self.return_url = return_url
        # 读取私钥
        with open(self.app_private_key_path) as fp:
            # 进行加密
            self.app_private_key = RSA.importKey(fp.read())

        self.alipay_public_key_path = alipay_public_key_path  # 公钥的文件
        # 读取公钥：验证支付宝返回的信息
        with open(self.alipay_public_key_path) as fp:
            self.alipay_public_key = RSA.import_key(fp.read())

        if debug is True:
            # 沙箱url
            self.__gateway = "https://openapi.alipaydev.com/gateway.do"
        else:
            # 真正的url
            self.__gateway = "https://openapi.alipay.com/gateway.do"

    def direct_pay(self, subject, out_trade_no, total_amount, return_url=None, **kwargs):
        ''' 请求参数 '''
        # 除了公共参数的其他参数：biz_content
        biz_content = {
            "subject": subject,
            "out_trade_no": out_trade_no,
            "total_amount": total_amount,
            "product_code": "FAST_INSTANT_TRADE_PAY",
            # "qr_pay_mode":4
        }
        # 可变参数[kwargs]；update(kwargs)：可以传递其他参数
        biz_content.update(kwargs)
        # 所有参数赋值给 data
        data = self.build_body("alipay.trade.page.pay", biz_content, self.return_url)
        # 参数进行签名处理，最后返回给view进行支付
        return self.sign_data(data)

    def build_body(self, method, biz_content, return_url=None):
        ''' 所有参数 '''

        data = {
            # 公共参数
            "app_id": self.appid,
            "method": method,  # 接口名称
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            # 请求参数
            "biz_content": biz_content
        }

        # url参数
        if return_url is not None:
            # 初始化的数据
            data["notify_url"] = self.app_notify_url
            data["return_url"] = self.return_url
        # 返回
        return data

    def sign_data(self, data):
        '''
            处理签名
            “%20”的字符不能进行处理，处理完后再生成“%20”
        '''

        # 签名不能有sign。pop：去掉列表的sign
        data.pop("sign", None)

        unsigned_items = self.ordered_data(data)  # 排序后的字符串
        # KEY和value之间用“=”隔开，KEY之间用&隔开
        unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)
        sign = self.sign(unsigned_string.encode("utf-8"))  # 签名字符类型

        # 生成“%20”的字符。将参数的url转化为“%20”的字符
        # quote：对有http等的url进行（转化为“%20”的字符）处理
        # quote_plus：它比quote多一些功能，将“空格”转换成“加号
        quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in unsigned_items)

        # 获得最终的订单信息字符串
        # 生成“%20”的字符。将签名转化为“%20”的字符
        signed_string = quoted_string + "&sign=" + quote_plus(sign)
        return signed_string

    def ordered_data(self, data):
        ''' 排序 '''
        complex_keys = []
        # 遍历每一个key，以字典的形式赋值给complex_keys
        for key, value in data.items():
            # isinstance:判断value是否是一个dict的类型
            if isinstance(value, dict):
                complex_keys.append(key)

        # 遍历所有的key
        for key in complex_keys:
            # separators：分隔符。keys之间用“,”隔开，而KEY和value之间用“：”隔开
            # 将data的字典类型的key数据dump出来：把字典转换为字符串
            data[key] = json.dumps(data[key], separators=(',', ':'))

        # sorted：默认小到大排序，类型为数组：[(k, v),(k, v)]
        return sorted([(k, v) for k, v in data.items()])

    def sign(self, unsigned_string):
        ''' 开始计算签名（生成签名） '''
        key = self.app_private_key  # 私钥
        signer = PKCS1_v1_5.new(key)  # 生成签名（私钥进行签名）的对象
        signature = signer.sign(SHA256.new(unsigned_string))  # 加密算法
        # base64 编码，转换为unicode表示并移除回车
        sign = encodebytes(signature).decode("utf8").replace("\n", "")
        return sign

    def _verify(self, raw_content, signature):
        # 开始计算签名
        key = self.alipay_public_key
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        digest.update(raw_content.encode("utf8"))
        if signer.verify(digest, decodebytes(signature.encode("utf8"))):
            return True
        return False

    def verify(self, data, signature):
        if "sign_type" in data:
            sign_type = data.pop("sign_type")
        # 排序后的字符串
        unsigned_items = self.ordered_data(data)
        message = "&".join(u"{}={}".format(k, v) for k, v in unsigned_items)
        return self._verify(message, signature)


if __name__ == "__main__":
    return_url = 'http://47.92.87.172:8000/?total_amount=0.01&timestamp=2017-08-15+17%3A15%3A13&sign=jnnA1dGO2iu2ltMpxrF4MBKE20Akyn%2FLdYrFDkQ6ckY3Qz24P3DTxIvt%2BBTnR6nRk%2BPAiLjdS4sa%2BC9JomsdNGlrc2Flg6v6qtNzTWI%2FEM5WL0Ver9OqIJSTwamxT6dW9uYF5sc2Ivk1fHYvPuMfysd90lOAP%2FdwnCA12VoiHnflsLBAsdhJazbvquFP%2Bs1QWts29C2%2BXEtIlHxNgIgt3gHXpnYgsidHqfUYwZkasiDGAJt0EgkJ17Dzcljhzccb1oYPSbt%2FS5lnf9IMi%2BN0ZYo9%2FDa2HfvR6HG3WW1K%2FlJfdbLMBk4owomyu0sMY1l%2Fj0iTJniW%2BH4ftIfMOtADHA%3D%3D&trade_no=2017081521001004340200204114&sign_type=RSA2&auth_app_id=2016080600180695&charset=utf-8&seller_id=2088102170208070&method=alipay.trade.page.pay.return&app_id=2016080600180695&out_trade_no=201702021222&version=1.0'

    # 测试用例
    alipay = AliPay(
        appid="2016092700609030",  # 沙箱的APPID
        app_notify_url="http://projectsedus.com/",  # vue的调用
        app_private_key_path="../trade/key/private_2048.txt",  # 自己生成的私钥
        alipay_public_key_path="../trade/key/alipay_key_2048.txt",  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        debug=True,  # debug为true时使用沙箱的url。如果不是用正式环境的url
        return_url="http://120.79.43.26/"  # 支付完成，转跳都到哪个页面
    )

    o = urlparse(return_url)
    query = parse_qs(o.query)
    processed_query = {}
    ali_sign = query.pop("sign")[0]
    for key, value in query.items():
        processed_query[key] = value[0]
    print(alipay.verify(processed_query, ali_sign))

    # 直接支付：direct_pay是生成请求的字符串
    url = alipay.direct_pay(
        subject="测试订单",  # 订单标题
        out_trade_no="201702021222",   # 我们商户自行生成的订单号
        total_amount=100000,  # 订单金额
        return_url='http://120.79.43.26/'
    )

    # 将生成请求的字符串，拿到我们的沙箱应用的url（支付宝网关）中进行拼接
    re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
    print(re_url)