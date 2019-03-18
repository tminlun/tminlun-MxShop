from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from utils.permissions import IsOwnerOrReadOnly
from .models import UserFav
from .serializers import UserFavSerializers,UserFavDetailSerializers

# Create your views here.


class UserFavViewSet(mixins.CreateModelMixin,mixins.DestroyModelMixin,mixins.ListModelMixin,mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    """
    create:
        商品的收藏
    delete:
        取消收藏
    list:
        把用户收藏列表展现出来
    retrieve:
        通过url的参数（goods_id）来判断某个商品是否收藏
    """
    # permission 是用来做权限判断的
    # IsAuthenticated 必须登录用户。IsOwnerOrReadOnly：必须是当前登录的用户
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    serializer_class = UserFavSerializers
    # auth用来做用户认证的。用户没有token是不能进行收藏的（坑）
    # 前端每一个request请求都加入我们的token的话，token恰好过期，用户访问goods列表页等不需要token认证的页面拿不到数据（抛异常）
    # SessionAuthentication: Django的默认身份验证（让用户可以登录）
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    # 这是一个查询具体对象：必须加RetrieveModelMixin（http://127.0.0.1:8000/userfavs/goods_id/）
    lookup_field = 'goods_id'  # url通过goods_id查询结果（相对于过滤过的UserFav查询的）

    def get_queryset(self):
        '''
        收藏和取消收藏的模型
        :return: 只能查看当前登录用户的收藏，不会获取到所有用户的收藏列表
        '''
        return UserFav.objects.filter(user=self.request.user)  # 只有重载才有request方法

    def get_serializer_class(self):
        ''' 动态区别serializer状态 '''
        if self.action == 'list':
            # 状态为详情信息，返回UserDetailSerialize
            return UserFavDetailSerializers
        elif self.action == 'create':
            return UserFavSerializers
        # 其他serializer状态
        return UserFavSerializers

