"""MxShop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
import xadmin
from django.urls import path, include, re_path
from django.conf import settings #上传图片
from django.conf.urls.static import static #上传图片
from django.views.generic import TemplateView
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token
from goods.views import GoodsListViewSet, CategoryViewSet
from users.views import SmsCodeViewSet, UserViewSet
from user_operation.views import UserFavViewSet,UserLeavingMessageViewSet,UserAddressViewSet
from trade.views import ShoppingCartViewSet,OrderInfoViewSet


router = DefaultRouter()  # 组合GenericViewSet方法，自动添加get、post、patch方法

router.register('goods', GoodsListViewSet,base_name='goods')  # 配置商品（坑：必须添加 base_name）
router.register('categorys', CategoryViewSet,base_name='categorys')  # 配置商品分类，RetrieveModelMixin：自动返回一个具体的实例
router.register('codes', SmsCodeViewSet,base_name='codes')  # 发送手机验证码
router.register('users', UserViewSet,base_name='users')  # 用户操作（注册，获取，修改...）
# 收藏
router.register('userfavs', UserFavViewSet,base_name='userfavs')
# 留言
router.register('messages', UserLeavingMessageViewSet,base_name='messages')
# 收货地址
router.register('address', UserAddressViewSet,base_name='address')
# 购物车管理
router.register('shopcarts', ShoppingCartViewSet, base_name="shopcarts")
# 订单管理
router.register('orders', OrderInfoViewSet, base_name="orders")


urlpatterns = [
    # 首页
    path('index/', TemplateView.as_view(template_name='index.html'), name='index'),

    path('xadmin/', xadmin.site.urls),


    # api显示登录按钮
    path('api-auth/', include('rest_framework.urls')),
    # 文档
    path('docs/',include_docs_urls(title='田田生鲜超市')),
    # 富文本编辑器url
    path('ueditor/',include('DjangoUeditor.urls')),

    # 商品列表页
    re_path('^', include(router.urls)),

    # # drf自带的token认证接口
    # path('api-token-auth/', views.obtain_auth_token),

    # jwt的token认证接口。前端登录的接口
    path('login/', obtain_jwt_token),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
