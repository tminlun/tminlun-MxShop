from datetime import datetime
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.permissions import IsOwnerOrReadOnly
from utils.alipay import AliPay
from MxShop.settings import ali_pub_key_path, private_key_path,notify_url,return_url

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

    '''
    改变商品库存数量：
        注：增删改购物车是单个商品
         1、添加购物车
         2、删除购物车
         3、修改购物车
    '''
    def perform_create(self, serializer):
        '''
            添加购物车，库存 - 购物车数量
        '''
        shop_cart = serializer.save()  # 购物车实例
        goods = shop_cart.goods  # 商品实例
        goods.goods_num -= shop_cart.nums  # shop_cart.nums：添加购物车时的数量
        goods.save()

    def perform_destroy(self, instance):
        '''
            删除购物车，库存 + 购物车数量
        instance：单个购物车实例
        '''
        # 库存增加删除前的购物车
        goods = instance.goods
        goods.goods_num += instance.nums
        goods.save()
        # 删除后的值，如在delete后增加商品库存数，则为0
        instance.delete()

    # 更新库存,修改可能是增加页可能是减少
    def perform_update(self, serializer):
        '''
        修改购物车
        :param serializer: 修改后的对象
        '''
        # 修改前的购物车对象
        existed_record = ShoppingCart.objects.get(id=serializer.instance.id)
        # 修改前的值
        existed_nums = existed_record.nums
        # 修改后的值（保存后的值）
        saved_record = serializer.save()

        # nums：修改后 - 修改前的差
        # saved_record.nums > existed_nums（nums：正数） ：增加购物车，减少库存
        # saved_record.nums < existed_nums（nums：负数） ：减少购物车，减少库存
        nums = saved_record.nums - existed_nums  # saved_record.nums ：修改后的数量；existed_nums：修改前的数量
        goods = saved_record.goods  # goods对象
        # 正数(购物车加)：库存数 - nums。负数（购物车减）：库存数 + nums
        goods.goods_num -= nums  # -= -nums 等于 += nums
        goods.save()


class OrderInfoViewSet(mixins.CreateModelMixin,mixins.ListModelMixin,mixins.DestroyModelMixin,mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    """
    订单管理
    akgami7604@sandbox.com
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
                order_goods.goods_num = shop_cart.nums  # 购物车总数量传递给订单商品总数量
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
            app_notify_url=notify_url,
            app_private_key_path=private_key_path,
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # 默认False,
            return_url=return_url
        )

        verify_re = alipay.verify(processed_dict, sign)

        # 这里可以不做操作。因为不管发不发return url。notify url都会修改订单状态。
        if verify_re is True:
            # 验证成功
            order_sn = processed_dict.get('out_trade_no', None)
            trade_no = processed_dict.get('trade_no', None)
            trade_status = processed_dict.get('trade_status', None)

            existed_orders = OrderInfo.objects.filter(order_sn=order_sn)
            for existed_order in existed_orders:
                existed_order.pay_status = trade_status
                existed_order.trade_no = trade_no
                existed_order.pay_time = datetime.now()
                existed_order.save()
            # response = redirect('index')
            # # 设置cookie让前端进行路由判断，max_age：取一次失效
            # response.set_cookie('nextPath', 'pay', max_age=2)
            response = redirect("/index/#/app/home/member/order")
            return response
        else:
            # 验证失败
            response = redirect('index')
            return response


    def post(self, request):
        '''
        处理支付宝的notify_url
        通过POST进行判断，通知商家是否支付成功
        扩展：为什么不能用本地调试，因为notify_url时返回给服务器的，而不是返回给浏览器处理，而且放在浏览器会不安全。
        第三方登录可以本地调试，是因为服务器只执行重定向操作，其他都是服务器处理，而且返回只是基本信息，并不是敏感信息。
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
            app_notify_url=notify_url,
            app_private_key_path=private_key_path,  # 自己生成的私钥
            alipay_public_key_path=ali_pub_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            debug=True,  # debug为true时使用沙箱的url。如果不是用正式环境的url
            # 同步url：电脑支付页面成功，回跳的url；（支付宝获取商家的return_url，通过GET请求返回部分支付信息）
            return_url=return_url
        )

        # 验证URL参数
        verify_re = alipay.verify(processed_dict, sign)
        # 验证成功
        if verify_re is True:
            # get：获取字典的元素
            # 先提交订单再进行支付，所以支付完成后就拿到自己生成的out_trade_no
            out_trade_no = processed_dict.get('out_trade_no', None)
            # 支付宝系统交易流水号
            trade_no = processed_dict.get('trade_no', None)
            # 交易状态
            trade_status = processed_dict.get('trade_status', None)
            # 查询数据库有此订单
            existed_orders = OrderInfo.objects.filter(trade_no=out_trade_no)
            for existed_order in existed_orders:
                # 支付成功再增加商品销量
                # 卖出n商品，即销售量为n
                order_goods = existed_order.goods.all()  # 所有订单商品对象（列表），OrderGoods外键是OrderInfo
                for order_good in order_goods:
                    goods = order_good.goods  # goods对象，OrderGoods外键是Goods
                    # 商品销售量 = 订单（卖出）所有商品数量
                    goods.sold_num += order_good.goods_num
                    goods.save()

                # 更新订单状态
                existed_order.pay_status = trade_status  # 订单状态（重点）
                existed_order.trade_no = trade_no  # 支付宝系统交易流水号
                existed_order.pay_time = datetime.now()  # 支付时间
                existed_order.save()
                # 需要返回一个'success'给支付宝，如果不返回，支付宝会一直发送订单支付成功的消息
            return Response("success")

