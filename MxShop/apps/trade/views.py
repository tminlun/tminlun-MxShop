from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins
from utils.permissions import IsOwnerOrReadOnly

from .models import ShoppingCart,OrderInfo,OrderGoods
from .serializers import ShoppingCartSerializer,ShoppingCartDetailSerializer,OrderInfoSerializer,OrderDetailSerializer
# Create your views here.


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """
    购物车操作
    list:
        获取购物车数据
    create:
        添加商品到购物车
    update:
        更改购物车（数量和价格）
    delete:
        删除单个购物车
    """
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)  # 权限验证
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)  # permission：用户验证（必须 登录、当前用户）
    serializer_class = ShoppingCartSerializer
    lookup_field = "goods_id"  # 通过goods_id来操作购物车详情，而不是默认的id

    def get_serializer_class(self):
        if self.action == 'list':
            # 购物车列表
            return ShoppingCartDetailSerializer
        else:
            # 添加、更新、删除购物车
            return ShoppingCartSerializer

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)


class OrderInfoViewSet(mixins.CreateModelMixin,mixins.ListModelMixin,mixins.DestroyModelMixin,mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    """
    订单管理
    update:
        订单不可以修改，不然价格被修改了怎么办
    list:
        获取订单数据
    create:
        创建订单
    delete:
        删除订单(order_info)的同时，会删除关联的，订单商品(order_goods)
    retrieve:
        订单详情,新添加serializer，来获得goods的数据
    """
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)  # 权限验证
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)  # permission：用户验证（必须 登录、当前用户）
    serializer_class = OrderInfoSerializer

    def get_serializer_class(self):
        '''订单详情，需要商品数据'''
        if self.action == 'retrieve':
            # 详情页，需要商品数据
            return OrderDetailSerializer
        # 订单的列表、创建、删除
        return OrderInfoSerializer

    def perform_create(self, serializer):
        '''
            serializer获取所有post数据，则执行此方法
            提交订单时，购物车数据保存到OrderInfo，再清空购物车
            注：我们只对购物车全部商品进行结算
        '''
        order = serializer.save()  # 获取serializer/Model的实例
        shop_carts = ShoppingCart.objects.filter(user=self.request.user)  # 购物车的所有商品
        if shop_carts:
            # 如果购物车有商品
            for shop_cart in shop_carts:
                # 购物车的单个实例,逐个的保存到，订单的单个实例
                order_goods = OrderGoods()
                order_goods.goods = shop_cart.goods
                order_goods.goods_num = shop_cart.nums
                order_goods.order = order
                order_goods.save()
                # 清空购物车
                shop_cart.delete()
        return order  # 订单信息保存数据库后，返回给前端

    def get_queryset(self):
        ''' 当前登录用户订单 '''
        return OrderInfo.objects.filter(user=self.request.user)
