# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/3/1 0001 19:49'
from django.db.models import Q
from rest_framework import serializers

from goods.models import Goods,GoodsCategory,GoodsImage,GoodsBanner,GoodsCategoryBrand,IndexAd


class GoodsCategorySerializer3(serializers.ModelSerializer):
    """
    三级分类
    """
    class Meta:
        model = GoodsCategory
        fields = '__all__'


class GoodsCategorySerializer2(serializers.ModelSerializer):
    """
    二级分类
    """
    # 通过二级分类反向查询第三级分类（GoodsCategory.sub_cat.sub_cat）
    sub_cat = GoodsCategorySerializer3(many=True)

    class Meta:
        model = GoodsCategory
        fields = '__all__'


class GoodsCategorySerializer(serializers.ModelSerializer):
    """
    一级分类：
        many=True：列表必须加
    """
    # 通过外键的related_name，查找到它的外键的全部有关于它的信息（GoodsCategory.sub_cat）,同时还把一二三级分类全部系列化出来
    # related_name="sub_cat"
    sub_cat = GoodsCategorySerializer2(many=True)

    class Meta:
        model = GoodsCategory
        fields = '__all__'


class GoodsImageSerializer(serializers.ModelSerializer):
    '''获取商品轮播图：goods的外键'''
    class Meta:
        model = GoodsImage
        fields = ('image',)


class GoodsSerializer(serializers.ModelSerializer):
    """
    系列化Goods列表
    """
    # 同ModelForms，可以添加字段（也可以实例化CategorySerializer的category）来覆盖默认的字段（Goods的category）
    category = GoodsCategorySerializer()
    # Goods.goods_banner
    '''
    goods_banner = GoodsImageSerializer(many=True):
        image = ImageField(allow_null=True, label='图片', max_length=200, required=False)
    '''
    goods_banner = GoodsImageSerializer(many=True)  # goods通过related_name,反向查询所有的商品图片

    class Meta:
        model = Goods
        fields = '__all__'


class GoodsBannerSerializer(serializers.ModelSerializer):
    """
    轮播图的系列化器
    """
    # 获取所有的goods数据
    goods = GoodsSerializer()

    class Meta:
        model = GoodsBanner
        fields = '__all__'


class CategoryBrandSerializer(serializers.ModelSerializer):
    '''
    首页类别广告的商标
    '''
    class Meta:
        model = GoodsCategoryBrand
        fields = '__all__'


class IndexCategorySerializer(serializers.ModelSerializer):
    '''
    首页类别广告：
    一级类，一级类里面有：
            商品商标（多个）
            大类下的二级类（多个）
            所有商品（多个）
            广告商品（单个）
    '''
    # 商品商标（多个）
    brands = CategoryBrandSerializer(many=True)  # GoodsCategory.brands
    # 大类下的二级类
    sub_cat = GoodsCategorySerializer2(many=True)  # GoodsCategory.sub_cat
    # 所有商品，SerializerMethodField自定义model没有的字段
    goods = serializers.SerializerMethodField()  # 这只能取出第三级分类下的商品，取不出一级类、二级类下的所有商品
    def get_goods(self, obj):
        '''
        取出一二三级分类的商品：
            获取到serializer（get_serializer），对queryset进行系列化。many=True是固定的：
                serializer = self.get_serializer(queryset, many=True)  # 实例
                    return Response(serializer.data)  实例的数据
        :param obj:  serializer的实例
        :return: Goods数据
        '''
        all_goods = Goods.objects.filter(Q(category_id=obj.id) | Q(category__parent_category_id=obj.id) | Q(
            category__parent_category__parent_category_id=obj.id))
        # 得到goods实例：获取到GoodsSerializer，对all_goods进行序列化。嵌套serializer要加context
        goods_serializer = GoodsSerializer(all_goods, many=True, context={'request': self.context['request']})
        # 得到goods数据,返回给goods
        return goods_serializer.data

    # 广告商品，只有一个图
    ad_goods = serializers.SerializerMethodField()
    def get_ad_goods(self, obj):
        '''
        广告的商品
        :param obj: GoodsCategory实例
        :return: 实例的数据
        '''

        goods_json = {}  # 返回json给前端
        # 商品广告当前的一级类的广告的商品
        ad_goods = IndexAd.objects.filter(category_id=obj.id, )
        if ad_goods:
            good_ins = ad_goods[0].goods  # 取到商品。因为ad_goods是list,所以要加[0]
            # 广告商品只有一个分类和一个商品：many=False
            # 在serializer里面调用serializer的话，就要添加一个参数context（上下文有request，则返回域名）,嵌套serializer必须加
            goods_json = GoodsSerializer(good_ins, many=False, context={'request': self.context['request']}).data
            # # 只返回id和image
            # goods_id = goods_json['id']
            # goods_image = goods_json['goods_front_image']
            # goods_list = [goods_id,goods_image]
            # goods_json = goods_list
        return goods_json

    class Meta:
        model = GoodsCategory
        fields = '__all__'
