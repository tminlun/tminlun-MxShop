# _*_ encoding:utf-8 _*_
__author__: '田敏伦'
__date__: '2019/4/10 0010 19:33'
import requests


class LoginTheory(object):
    """
        微博、QQ、微信登录的原理
        进行登录，登录获取access_token，使用access_token来获取当前登录的用基本信息
    """
    def __init__(self,client_id,redirect_uri,grant_type):
        self.client_id = client_id   # 申请应用时分配的AppKey
        self.redirect_uri = redirect_uri  # 授权回调地址
        self.grant_type = grant_type  # 授权回调地址

    def get_auth_url(self, weibo_auth_url):
        """
        进行登录，请求用户授权authorize
        :return:
        """
        weibo_auth_url = weibo_auth_url
        client_id = self.client_id
        redirect_uri = self.redirect_uri
        auth_url = weibo_auth_url+"?client_id={client_id}&redirect_uri={redirect_uri}".format(client_id=client_id, redirect_uri=redirect_uri)
        print(auth_url)

    def token_url(self,access_token_url,code):
        """
        获取当前登录才能得到的用户信息
        :param code:调用authorize获得的code值。
        :return: access_token
        """
        # URL
        access_token_url = access_token_url
        # 参数
        parmas = {
            "client_id": self.client_id,
            "client_secret": "0463730f8aad338fabd367069687b9f4",  # 申请应用时分配的AppSecret。
            "grant_type": self.grant_type,  # 请求的类型,固定的
            "code": code,  # 调用authorize获得的code值。
            "redirect_uri": self.redirect_uri,  # 回调的url
        }
        # HTTP请求方式
        re_dict = requests.post(access_token_url, data=parmas)
        '{"access_token":"2.00gKH_lGxIvvbC8f72cf2d4bGTF7JC","remind_in":"157679999","expires_in":157679999,"uid":"6195840586","isRealName":"true"}'
        pass

    def get_user_show(self,user_show_url,access_token,uid):
        user_show_url = user_show_url
        re_dict = user_show_url+"?access_token={token}&uid={uid}".format(token=access_token, uid=uid)
        print(re_dict)


def main():
    theory = LoginTheory(2392794455,"http://120.79.43.26/complete/weibo/", "authorization_code")
    # theory.get_auth_url(weibo_auth_url = "https://api.weibo.com/oauth2/authorize")
    # theory.token_url(access_token_url = "https://api.weibo.com/oauth2/access_token",code="672569526598fa452bd59372f39a51ac")
    theory.get_user_show(user_show_url="https://api.weibo.com/2/users/show.json", access_token="2.00gKH_lGxIvvbC8f72cf2d4bGTF7JC", uid="6195840586")


if __name__ == '__main__':
    main()
