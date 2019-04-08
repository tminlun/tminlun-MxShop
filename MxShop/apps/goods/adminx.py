# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/2/27 0027 13:19'

#!/usr/bin/env python
# encoding: utf-8

"""
@version: 1.0
@author: liyao
@license: Apache Licence 
@contact: yli@posbao.net
@site: http://www.piowind.com/
@software: PyCharm
@file: adminx.py
@time: 2017/7/4 17:04
"""
import xadmin
from .models import Goods, GoodsCategory, GoodsImage, GoodsCategoryBrand, GoodsBanner,IndexAd


class GoodsAdmin(object):
    list_display = ["name", "click_num", "sold_num", "fav_num", "goods_num", "market_price",
                    "shop_price", "goods_brief", "goods_descs", "is_new", "is_hot", "add_time"]
    search_fields = ['name', ]
    list_editable = ["is_hot", ]
    list_filter = ["name", "click_num", "sold_num", "fav_num", "goods_num", "market_price",
                   "shop_price", "is_new", "is_hot", "add_time", "category__name"]
    style_fields = {"goods_desc": "ueditor"}

    class GoodsImagesInline(object):
        model = GoodsImage
        exclude = ["add_time"]
        extra = 1
        style = 'tab'

    inlines = [GoodsImagesInline]


class GoodsCategoryAdmin(object):
    list_display = ["name", "category_type", "parent_category", "add_time"]
    list_filter = ["category_type", "parent_category", "name"]
    search_fields = ['name', ]


class GoodsBrandAdmin(object):
    list_display = ["category", "image", "name", "desc"]

    # 重载get_context方法
    def get_context(self):
        '''
        只能选择一级分类
        :return:
        '''
        context = super(GoodsBrandAdmin, self).get_context()  # 调用父类
        if 'form' in context:
            # if 'form' in context:：固定写法
            context['form'].fields['category'].queryset = GoodsCategory.objects.filter(category_type=1)#对fields['category']字段做处理
        return context


class GoodsBannerAdmin(object):
    list_display = ["goods", "image", "index"]


class IndexAdAdmin(object):
    list_display = ["category", "goods"]


xadmin.site.register(Goods, GoodsAdmin)
xadmin.site.register(GoodsCategory, GoodsCategoryAdmin)
xadmin.site.register(GoodsBanner, GoodsBannerAdmin)
xadmin.site.register(GoodsCategoryBrand, GoodsBrandAdmin)
xadmin.site.register(IndexAd, IndexAdAdmin)




