# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/3/19 0019 22:54'
import time
import re
from rest_framework import serializers
from goods.models import Goods
from goods.serializers import GoodsSerializer
from MxShop.settings import REGEX_MOBILE
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
        :return:
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