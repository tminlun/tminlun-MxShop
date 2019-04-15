# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/3/19 0019 22:54'
import time
import re
from rest_framework import serializers
from goods.models import Goods
from goods.serializers import GoodsSerializer
from MxShop.settings import REGEX_MOBILE
from utils.alipay import AliPay
from MxShop.settings import ali_pub_key_path, private_key_path,notify_url,return_url

from .models import ShoppingCart,OrderInfo,OrderGoods


class ShoppingCartDetailSerializer(serializers.ModelSerializer):
    """
    购物车列表页面
    通过重写的goods获得goods_id，来获取goods详情的url和数据
    """
    # read_only：不需要用户填写，由后端给api
    goods = GoodsSerializer(many=False, read_only=True)  # 购物车一次添加，只能添加单个商品（一个购物车对应一个商品）

    class Meta:
        model = ShoppingCart
        fields = "__all__"


class ShoppingCartSerializer(serializers.Serializer):
    """
    添加和修改购物车
    使用Serializer：
        根据需求，必须重写create、update
        因为联合唯一有相同记录时（添加多次通条数据），用ModelSerializer的validated_data会默认报错，则不执行create函数
    """
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    # 添加购物车，商品数量必须 + 1。数量不能为0
    nums = serializers.IntegerField(required=True,min_value=1,label="数量",
                                          error_messages={
                                              'required': '请填写购买商品的数量',
                                              'min_value': '购物车商品数量不能小于一',
                                          }, help_text='购物车商品数量')
    goods = serializers.PrimaryKeyRelatedField(required=True, queryset=Goods.objects.all(),help_text="商品")  # 此为外键goods模型

    def create(self, validated_data):
        '''
        Serializer添加商品：则手动实现create方法
        :param validated_data: 已经处理过的数据（用户post来的值）
        :return: 创建记录
        '''
        # Serializer的self没有request属性，context['request']即request
        user = self.context['request'].user
        nums = validated_data['nums']
        goods = validated_data['goods']

        # 如果购物车中有记录，数量+1
        # 如果购物车车没有记录，就创建
        existed = ShoppingCart.objects.filter(user=user, goods=goods)
        if existed:
            # 再次添加同一个商品，则数量加一
            existed = existed[0]  # 最新添加购物车的记录
            # nums：用户post的数量，默认为1
            existed.nums += nums
            existed.save()
        else:
            # 无记录
            existed = ShoppingCart.objects.create(**validated_data)
            existed.save()
        # 验证完添加商品记录返回给前端
        return existed

    def update(self, instance, validated_data):
        '''
        Serializer默认不重写update、create方法。如果要进行这些操作，必须手动添加
        :param instance: 当前类的，model实例
        :param validated_data: 用户put的数据
        :return: 修改购物车数量
        '''
        instance.nums = validated_data['nums']
        return instance


class OrderGoodsSerializer(serializers.ModelSerializer):
    '''
    订单所有商品。重写goods字段名，获取到商品的具体数据
    '''
    # many=False：因为购物车的商品，逐个的保存逐个OrderGoods实例
    # 一个OrderGoods实例，对应一个商品。而不是一个OrderGoods实例对应多个商品
    goods = GoodsSerializer(many=False)

    class Meta:
        model = OrderGoods
        fields = "__all__"


class OrderDetailSerializer(serializers.ModelSerializer):
    '''
    订单详情
    通过关联的OrderGoods模型，反向系列化（order=related_name=“goods”）所有的OrderGoods实例
    OrderInfo.goods：可得到当前订单的，所有的商品
    '''
    # many=True：一个订单对应多个商品
    # goods[goods1,goods2...]（goods[OrderGoods1,OrderGoods2]）
    goods = OrderGoodsSerializer(many=True)

    # 个人订单详情，未支付可以在个人订单支付
    alipay_url = serializers.SerializerMethodField(read_only=True)
    def get_ailpay_url(self, obj):
        """
        系列化ailpay_url，返回ailpay_url（数据）给前端
        :param obj: 当前函数对象
        :return: 支付页面
        """
        # AliPay对象
        alipay = AliPay(
            appid="2016092700609030",  # 沙箱的APPID
            # 异步url：支付宝获取商家传递的notify_url，通过POST进行判断，通知商家是否支付成功，
            # 另外的用途：用户扫码(没有进行支付),支付宝会生成订单url，用户可以通过此url进行支付或者修改订单
            app_notify_url=notify_url,
            app_private_key_path=private_key_path,  # 自己生成的私钥
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # debug为true时使用沙箱的url。如果不是用正式环境的url
            # 同步url：电脑支付页面成功，回跳的url；（支付宝获取商家的return_url，通过GET请求返回部分支付信息）
            return_url=return_url
        )
        # 请求参数
        url = alipay.direct_pay(
            subject=obj.order_sn,  # 订单标题
            out_trade_no=obj.order_sn,  # 我们商户自行生成的订单号
            total_amount=obj.order_mount,  # 订单金额
            return_url=return_url
        )
        re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
        return re_url

    class Meta:
        model = OrderInfo
        fields = "__all__"


class OrderInfoSerializer(serializers.ModelSerializer):
    """
    订单列表、添加、修改、删除
    """
    # 当前用户
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    # 只读不写
    order_sn = serializers.CharField(read_only=True)

    nonce_str = serializers.CharField(read_only=True)
    trade_no = serializers.CharField(read_only=True)
    pay_status = serializers.CharField(read_only=True)
    pay_time = serializers.CharField(read_only=True)
    add_time = serializers.CharField(read_only=True)

    # 支付宝支付的url（新增数据库没有的字段）
    ailpay_url = serializers.SerializerMethodField(read_only=True)

    def get_ailpay_url(self, obj):
        """
        系列化ailpay_url，返回ailpay_url（数据）给前端
        :param obj: 当前函数对象
        :return: 支付页面
        """
        # AliPay对象
        alipay = AliPay(
            appid="2016092700609030",  # 沙箱的APPID
            # 异步url：支付宝获取商家传递的notify_url，通过POST进行判断，通知商家是否支付成功，
            # 另外的用途：用户扫码(没有进行支付),支付宝会生成订单url，用户可以通过此url进行支付或者修改订单
            app_notify_url=notify_url,
            app_private_key_path=private_key_path,  # 自己生成的私钥
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # debug为true时使用沙箱的url。如果不是用正式环境的url
            # 同步url：电脑支付页面成功，回跳的url；（支付宝获取商家的return_url，通过GET请求返回部分支付信息）
            return_url=return_url
        )
        # 请求参数
        url = alipay.direct_pay(
            subject=obj.order_sn,  # 订单标题
            out_trade_no=obj.order_sn,  # 我们商户自行生成的订单号
            total_amount=obj.order_mount,  # 订单金额
            return_url=return_url
        )
        re_url = "https://openapi.alipaydev.com/gateway.do?{data}".format(data=url)
        return re_url

    def validate_singer_mobile(self, singer_mobile):
        '''验证号码'''
        if not re.match(REGEX_MOBILE, singer_mobile):
            # 验证出错
            raise serializers.ValidationError('号码格式错误')
        return singer_mobile

    def generate_order_sn(self):
        '''生成订单号'''
        from random import Random
        random_ins = Random()
        order_sn = "{time_str}{user_id}{random_str}".format(time_str=time.strftime('%Y%m%d%H%M%S'),
                                                            user_id=self.context['request'].user.id,
                                                            random_str=random_ins.randint(10,99))
        return order_sn

    def validate(self, attrs):
        """
        需要验证两个字段：validate做了逻辑后（获取所有数据后），然后就在views中就可以save（保存到数据库）
        :param attrs: 所有验证过并post的值
        :return: attrs
        """
        attrs["order_sn"] = self.generate_order_sn()  # 后端生成订单号
        return attrs

    class Meta:
        model = OrderInfo
        fields = "__all__"
