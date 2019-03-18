# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/3/14 0014 20:06'

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from goods.serializers import GoodsSerializer
from .models import UserFav


class UserFavDetailSerializers(serializers.ModelSerializer):
    '''
    每个serializers都是一个记录
    显示用户收藏列表（收藏全部字段）
    '''
    # 一个收藏记录是对应一个goods对象（商品详情页：一个收藏只能收藏一个goods）
    goods = GoodsSerializer()

    class Meta:
        model = UserFav
        fields = ("goods", "id")


class UserFavSerializers(serializers.ModelSerializer):
    """
    收藏直接保存全部数据，ModelSerializer合适
    """

    # 设置当前登录用户来，进行收藏
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
        fields = ("user", "goods", "id")  # 取消功能需要id
