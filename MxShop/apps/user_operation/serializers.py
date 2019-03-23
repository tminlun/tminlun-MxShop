# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/3/14 0014 20:06'

import re
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from MxShop.settings import REGEX_MOBILE
from goods.serializers import GoodsSerializer
from .models import UserFav,UserLeavingMessage,UserAddress


class UserFavDetailSerializers(serializers.ModelSerializer):
    '''
    为了显示收藏商品的goods详情
    每个serializers都是一个记录
    显示用户收藏列表（收藏全部字段）
    '''
    # 一个收藏记录是对应一个goods对象（商品详情页：收藏一次只能收藏一个goods）
    goods = GoodsSerializer()

    class Meta:
        model = UserFav
        fields = ("goods", "id")


class UserFavSerializers(serializers.ModelSerializer):
    """
    收藏直接保存全部数据，ModelSerializer合适

    """

    # 设置当前登录用户，才能进行收藏
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        # 自己定义：模型不能有相同记录（其实有默认验证：unique_together）
        # 为什么不放在"单个字段"里面，因为成唯一集合的“集合需要两个字段”
        validators = [
            UniqueTogetherValidator(
                queryset=UserFav.objects.all(),
                fields=('user', 'goods'),  # 对构成唯一集合的字段,一个用户不能收藏两次同个商品
                message="已经收藏"
            )
        ]

        model = UserFav
        # user：返回api（当前登录收藏商品的用户）给前端
        fields = ("user", "goods", "id")  # 取消功能需要id


class UserLeavingMessageSerializers(serializers.ModelSerializer):
    '''
    get:
        将model实例和queryset进行系列化，通过json返回给用户（ API接口）
    post/ patch
        进行：数据验证和数据处理
    当前登录用户留言
    '''

    # 当前登录用户留言
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    # read_only：不需要用户自己上传，只能服务端通过api输出
    # write_only：用户post过来的值，后台经过处理后不会经过系列化后返回给客户端（最常见的就是手机注册的验证码和密码）
    add_time = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')  # 返回api（add_time）给前端

    class Meta:
        model = UserLeavingMessage
        fields = ("user", "message_type", "subject", "message", "file", "add_time", "id")  # 取消功能需要id


class UserAddressSerializers(serializers.ModelSerializer):
    ''' 收货地址管理验证 '''

    # 当前用户
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    # 验证名称：allow_blank不能为空
    signer_name = serializers.CharField(allow_blank=True,required=True,max_length=10,
                                        error_messages = {
                                            "blank": "输入不能为空",
                                            "required": "请输入验证码",
                                            "max_length": "名称格式错误",
                                        },
                                     help_text="收货姓名",label="收货姓名")

    # 验证收货号码
    signer_mobile = serializers.CharField(max_length=11)

    def validate_signer_mobile(self, signer_mobile):
        '''
        验证 signer_mobile（validate_ + 字段名）
        如果不return，则用户输入的内容不保存到数据库
        '''
        if not re.match(REGEX_MOBILE, signer_mobile):
            # 判断号码是否合法。如果号码第一个匹配不正确，则抛出异常
            raise serializers.ValidationError("手机号码非法")
        return signer_mobile  # 注意：必须return（这是一个大坑）

    add_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = UserAddress
        # 验证完字段，返回api给前端
        fields = ("id","user", "province", "city", "district", "address", "signer_name", "signer_mobile", "add_time")
