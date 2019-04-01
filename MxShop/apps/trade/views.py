from datetime import datetime
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.permissions import IsOwnerOrReadOnly
from utils.alipay import AliPay
from MxShop.settings import ali_pub_key_path, private_key_path

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
                order_goods.order = order  # 商品放在哪个订单
                order_goods.save()
                # 清空购物车
                shop_cart.delete()
        return order  # 订单信息保存数据库后，返回给前端

    def get_queryset(self):
        ''' 当前登录用户订单 '''
        return OrderInfo.objects.filter(user=self.request.user)


class AlipayView(APIView):
    """先判断是否支付成功。如果支付成功，再验证支付成功返回的支付信息(re_url)"""
    def get(self, request):
        '''
        处理支付宝的return_url
        通过GET请求返回部分支付信息
        '''
        processed_dict = {}
        # 1. 获取GET中参数
        for key, value in request.GET.items():
            processed_dict[key] = value
        # 2. 取出sign
        sign = processed_dict.pop("sign", None)

        # 3. 生成ALipay对象
        alipay = AliPay(
            appid="2016092700609030",  # 沙箱的APPID
            app_notify_url="http://120.79.43.26/alipay/return/",
            app_private_key_path=private_key_path,
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # 默认False,
            return_url="http://120.79.43.26/alipay/return/"
        )

        verify_re = alipay.verify(processed_dict, sign)

        # 这里可以不做操作。因为不管发不发return url。notify url都会修改订单状态。
        if verify_re is True:
            order_sn = processed_dict.get('out_trade_no', None)
            trade_no = processed_dict.get('trade_no', None)
            trade_status = processed_dict.get('trade_status', None)

            existed_orders = OrderInfo.objects.filter(order_sn=order_sn)
            for existed_order in existed_orders:
                existed_order.pay_status = trade_status
                existed_order.trade_no = trade_no
                existed_order.pay_time = datetime.now()
                existed_order.save()
            return Response("success")

    def post(self, request):
        '''
        处理支付宝的notify_url
        通过POST进行判断，通知商家是否支付成功
        '''

        processed_dict = {}
        for key, value in request.POST.items():
            # django的request默认把请求（返回url参数）列表转换为字符串
            # 循环出URL的参数
            processed_dict[key] = value
        # URL参数里的sign参数
        sign = processed_dict.pop('sign', None)

        # 生成一个Alipay对象
        alipay = AliPay(
            appid="2016092700609030",  # 沙箱的APPID
            # 异步url：支付宝获取商家传递的notify_url，通过POST进行判断，通知商家是否支付成功，
            # 另外的用途：用户扫码(没有进行支付),支付宝会生成订单url，用户可以通过此url进行支付或者修改订单
            app_notify_url="http://120.79.43.26:8001/alipay/return/",
            app_private_key_path=private_key_path,  # 自己生成的私钥
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # debug为true时使用沙箱的url。如果不是用正式环境的url
            # 同步url：电脑支付页面成功，回跳的url；（支付宝获取商家的return_url，通过GET请求返回部分支付信息）
            return_url="http://120.79.43.26:8001/alipay/return/"
        )

        # 验证URL参数
        verify_re = alipay.verify(processed_dict, sign)
        # 验证成功
        if verify_re is True:
            # get：获取字典的元素
            # 自己生成的唯一订单号
            out_trade_no = processed_dict.get('out_trade_no', None)
            # 支付宝系统交易流水号
            trade_no = processed_dict.get('trade_no', None)
            # 交易状态
            trade_status = processed_dict.get('trade_status', None)
            # 查询数据库的订单记录
            existed_orders = OrderInfo.objects.filter(trade_no=out_trade_no)
            for existed_order in existed_orders:
                # 更新订单状态
                existed_order.pay_status = trade_status
                existed_order.trade_no = trade_no
                existed_order.pay_time = datetime.now()
                existed_order.save()
                # 需要返回一个'success'给支付宝，如果不返回，支付宝会一直发送订单支付成功的消息
            return Response("success")

