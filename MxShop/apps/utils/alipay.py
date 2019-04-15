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
    逻辑：什么接口都是：应用的url拼接必填参数
    初始化数据（app_notify_url、app_private_key、alipay_public_key、return_url） --
     生成参数（公共参数和请求参数）--
     参数通过
     验签
     （
        除去sign、将剩下参数进行url_decode、KEY之间用&隔开、字典排序、组成字符串，得到待签名字符串、
        将签名字符串base64解码为字节码串、字节码串进行RSA加密
    ）
     处理后，返回给 direct_pay --
    view传递初始化数据，调用direct_pay直接支付

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
        '''
            传递参数而进行签名处理，处理后的字符串（签名字符串和参数字符串）返回给direct_pay
            direct_pay直接字符
         '''
        # 请求参数：biz_content
        biz_content = {
            "subject": subject,  # 订单标题
            "out_trade_no": out_trade_no,  # 商户订单号，不得有相同订单号
            "total_amount": total_amount, # 订单金额
            "product_code": "FAST_INSTANT_TRADE_PAY",  # 销售产品码
            # "qr_pay_mode":4
        }
        # 可变参数[kwargs]；update(kwargs)：可以传递其他参数
        biz_content.update(kwargs)
        # 所有参数赋值给 data
        data = self.build_body("alipay.trade.page.pay", biz_content, self.return_url)
        #
        return self.sign_data(data)

    def build_body(self, method, biz_content, return_url=None):
        ''' 生成消息的格式（utf、RSA2） '''
        # 公共参数
        data = {
            # 公共参数
            "app_id": self.appid,  # 支付宝分配给开发者的应用ID
            "method": method,  # 接口名称
            "charset": "utf-8",  # 请求使用的编码格式
            "sign_type": "RSA2",  # 签名算法类型
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 发送请求的时间
            "version": "1.0",  # 调用的接口版本
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
            订单信息的字符串
            除去sign
            将剩下参数进行url_decode, 然后进行字典排序，组成字符串，得到待签名字符串
        '''

        # 字符串
        # 要得到签名，不能有sign。pop：去掉列表的sign
        data.pop("sign", None)
        # 排序后的字符串
        unsigned_items = self.ordered_data(data)
        # 排序后的字符串进行&连接： KEY和value之间用“=”隔开，KEY之间用&隔开
        unsigned_string = "&".join("{0}={1}".format(k, v) for k, v in unsigned_items)

        # 得到签名
        sign = self.sign(unsigned_string.encode("utf-8"))

        # 处理url（将参数的url转化为“%20”的字符）
        # quote：对有http等的url进行（转化为“%20”的字符）处理
        # quote_plus：它比quote多一些功能，将“空格”转换成“加号
        quoted_string = "&".join("{0}={1}".format(k, quote_plus(v)) for k, v in unsigned_items)

        # 订单信息的字符串
        # 将签名的url转化为“%20”的字符
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
        '''
        生成签名字符串：
         将签名参数（sign）使用base64解码为字节码串。
        '''
        key = self.app_private_key  # 私钥
        signer = PKCS1_v1_5.new(key)  # 生成签名的对象
        signature = signer.sign(SHA256.new(unsigned_string))  # 加密算法
        # base64 编码，转换为unicode表示并移除回车
        sign = encodebytes(signature).decode("utf8").replace("\n", "")
        return sign

    def _verify(self, raw_content, signature):
        '''
            验证返回url是否合法
            获取re_url参数，使用支付宝生成公钥进行签名（返回的url参数，是否为支付宝传递的url参数）
            支付宝正确签名完的参数，跟返回url的参数进行匹配
            :raw_content re_url的字符串
            :signature 支付宝的字符串
        '''
        # 生成验证对象：digest
        key = self.alipay_public_key
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        # 订单字符串
        digest.update(raw_content.encode("utf8"))
        # 将digest和signature进行对比
        if signer.verify(digest, decodebytes(signature.encode("utf8"))):
            # 验证成功
            return True
        return False

    def verify(self, data, signature):
        '''
        处理过的data、signature，返回给_verify
        :param data: 服务端的url
        :param signature:支付宝的字符串
        :return:传递给_verify
        '''
        # 使用RSA的验签方法，通过签名字符串、签名参数（经过base64解码）及支付宝公钥验证签名【_verify】。
        if "sign_type" in data:
            # sign_type：RSA2
            sign_type = data.pop("sign_type")
        # 排序后的支付宝字符串
        unsigned_items = self.ordered_data(data)
        message = "&".join(u"{}={}".format(k, v) for k, v in unsigned_items)
        return self._verify(message, signature)


if __name__ == "__main__":
    # views通过GET请求获取return_url
    return_url = 'http://47.92.87.172:8000/?total_amount=0.01&timestamp=2017-08-15+17%3A15%3A13&sign=jnnA1dGO2iu2ltMpxrF4MBKE20Akyn%2FLdYrFDkQ6ckY3Qz24P3DTxIvt%2BBTnR6nRk%2BPAiLjdS4sa%2BC9JomsdNGlrc2Flg6v6qtNzTWI%2FEM5WL0Ver9OqIJSTwamxT6dW9uYF5sc2Ivk1fHYvPuMfysd90lOAP%2FdwnCA12VoiHnflsLBAsdhJazbvquFP%2Bs1QWts29C2%2BXEtIlHxNgIgt3gHXpnYgsidHqfUYwZkasiDGAJt0EgkJ17Dzcljhzccb1oYPSbt%2FS5lnf9IMi%2BN0ZYo9%2FDa2HfvR6HG3WW1K%2FlJfdbLMBk4owomyu0sMY1l%2Fj0iTJniW%2BH4ftIfMOtADHA%3D%3D&trade_no=2017081521001004340200204114&sign_type=RSA2&auth_app_id=2016080600180695&charset=utf-8&seller_id=2088102170208070&method=alipay.trade.page.pay.return&app_id=2016080600180695&out_trade_no=201702021222&version=1.0'

    # 测试用例
    # 必须填写异步、同步的url：确保可以进入views接口逻辑
    alipay = AliPay(
        appid="2016092700609030",  # 沙箱的APPID
        # 异步url：支付宝获取商家传递的notify_url，通过POST进行判断，通知商家是否支付成功，
        # 另外的用途：用户扫码(没有进行支付),支付宝会生成订单url，用户可以通过此url进行支付或者修改订单
        app_notify_url="http://120.79.43.26/alipay/return/",
        app_private_key_path="../trade/key/private_2048.txt",  # 自己生成的私钥
        alipay_public_key_path="../trade/key/alipay_key_2048.txt",  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        debug=True,  # debug为true时使用沙箱的url。如果不是用正式环境的url
        # 同步url：电脑支付页面成功，回跳的url；（支付宝获取商家的return_url，通过GET请求返回部分支付信息）
        return_url="http://120.79.43.26:8001/alipay/return/"
    )

    # 将同步支付通知url,传到urlparse
    o = urlparse(return_url)
    # 获取到URL的各种参数
    query = parse_qs(o.query)
    # 定义一个字典来存放，循环获取到的URL参数
    processed_query = {}
    # 将URL参数里的sign字段拿出来
    ali_sign = query.pop("sign")[0]

    # 直接支付
    # direct_pay是生成请求的字符串
    url = alipay.direct_pay(
        subject="测试订单",  # 订单标题
        out_trade_no="2017020212cc",   # 我们商户自行生成的订单号
        total_amount=1,  # 订单金额
        return_url='http://120.79.43.26:8001'
    )

    # 循环出URL里的参数
    for key, value in query.items():
        # 将循环到的参数，以键值对形式追加到processed_query字典
        processed_query[key] = value[0]  # python脚本返回数组，但是在Django自动转为字符串
        # 将循环组合的参数字典，以及拿出来的sign字段，传进支付类里的verify方法，返回验证合法性，返回布尔值，True为合法，表示支付确实成功了，这就是验证是否是伪造支付成功请求
    print(alipay.verify(processed_query, ali_sign))

    # 将生成请求的字符串，拿到我们的沙箱应用的url（支付宝网关）中进行拼接
    re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
    print(re_url)
