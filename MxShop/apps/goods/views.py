from rest_framework.views import APIView  # 和View功能一样，是View的进阶版
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet
from rest_framework import filters  # 搜索
from rest_framework.authentication import TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend  # 过滤+
# 和Django的forms、modelsforms功能一样
from goods.serializers import GoodsSerializer, GoodsCategorySerializer,GoodsBannerSerializer, IndexCategorySerializer
from .models import Goods, GoodsCategory,GoodsBanner
from .filters import GoodsFilter
# Create your views here.


class GoodsPagination(PageNumberPagination):
    '''
    自定义分页（有了自定义分页，可以注释setting的分页了）
    '''
    # 默认每页显示的个数
    page_size = 12
    # 让前端（用户）可以手动 动态改变每页显示的个数：&page_size=?
    page_size_query_param = 'page_size'
    # 页码的参数（url的参数page=?）
    page_query_param = 'page'
    # 最多能显示100页
    max_page_size = 100


class GoodsListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    '''
    list:
        View就是接口
        商品列表,这里可以在drf显示哦；GenericViewSet：自动生成get...方法
    retrieve:
        返回商品详情页,不需要添加url（但是serializer要改变，因为goods有个image轮播图）
    '''
    queryset = Goods.objects.all().order_by('-id')  # model就行系列化，转换为json，返回给用户（api接口）
    serializer_class = GoodsSerializer  # get()：系列化（加工）
    pagination_class = GoodsPagination  # 实现分页

    # DRF的过滤、搜索、排序，只需要在此（filter_backends）添加属性
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    #  自定义的过滤类
    filterset_class = GoodsFilter
    # 搜索：默认为模糊查询，~name：name前几个字符要和输入的字符匹配；=name：精准搜索
    search_fields = ('name', 'goods_brief', 'goods_desc')
    # 排序
    ordering_fields = ('sold_num', 'shop_price')


class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """
    list:
        获取商品分类数据（这样注释后面读取dosc文档的时候会显示出来）
    retrieve:
        自动返回一个具体的实例
        GenericViewSet：自动生成get方法
    """
    queryset = GoodsCategory.objects.filter(category_type=1)  # 最初先系列化一级分类
    serializer_class = GoodsCategorySerializer  # 系列化


class GoodsBannerViewSet(mixins.ListModelMixin,GenericViewSet):
    '''
    list:
        获取轮播图数据
    '''
    queryset = GoodsBanner.objects.all().order_by('index')
    serializer_class = GoodsBannerSerializer


class IndexCategoryViewSet(mixins.ListModelMixin, GenericViewSet):
    '''
    list:
        首页商品分类广告数据
    '''

    # 只选取轮播类别；只选取两个大类进行
    queryset = GoodsCategory.objects.filter(is_banner=True, name__in=['生鲜食品', '酒水饮料'])
    # 得到系列化数据
    serializer_class = IndexCategorySerializer

