# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/3/14 0014 23:06'

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    比对删除是否为当前用户：删除收藏的用户是否为当前登录的用户。
    如果不是当前用户会返回404错误
    判断用户是否是当前request的用户
    """

    def has_object_permission(self, request, view, obj):
        # obj：模型
        if request.method in permissions.SAFE_METHODS:
            # 如果登录的状态是安全性的（'GET', 'HEAD', 'OPTIONS'）
            return True

        # Instance must have an attribute named `owner`.
        return obj.user == request.user  # 在此修改owner为user