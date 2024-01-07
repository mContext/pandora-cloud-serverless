import os
from os.path import join, abspath, dirname

import httpx
import requests
from flask import request, jsonify
from pandora.exts.config import USER_CONFIG_DIR
from pandora.exts.token import check_access_token_out, check_access_token
from pandora.launcher import read_access_token, save_access_token
from pandora.openai.api import ChatGPT
from pandora_cloud.server import ChatBot as CloudServer
from waitress import serve

ACCESS_TOKEN = None


def get_access_token(refresh_token: str):
    default_token_file = os.path.join(USER_CONFIG_DIR, 'access_token.dat')
    if os.path.exists(default_token_file):
        access_token = read_access_token(default_token_file)
    else:
        access_token = None
    if not access_token or not check_access_token_out(access_token):
        access_token = requests.post(
            'https://ai.fakeopen.com/auth/refresh',
            data={'refresh_token': refresh_token}
        ).json().get('access_token', '')
        save_access_token(access_token)
    return access_token


# def get_access_token(refresh_token: str):
#     global ACCESS_TOKEN
#     if not ACCESS_TOKEN or not check_access_token_out(ACCESS_TOKEN):
#         ACCESS_TOKEN = requests.post(
#             'https://ai.fakeopen.com/auth/refresh',
#             data={'refresh_token': refresh_token}
#         ).json().get('access_token', '')
#     return ACCESS_TOKEN


class MyCloudServer(CloudServer):
    def __init__(self, refresh_token: str, debug=True):
        self.refresh_token = refresh_token
        super().__init__(None, debug=debug)

    async def login_token(self):
        access_token = request.form.get('access_token')
        next_url = request.form.get('next')
        error = None

        if access_token:
            try:
                # modify by xuqiao
                if access_token == 'ouzhoumma':
                    access_token = get_access_token(self.refresh_token)
                elif 0 < len(access_token) < 20:
                    access_token = await self.generate_share_token(access_token)
                # end modify
                payload = check_access_token(access_token)
                if payload is True:
                    ti = await super(MyCloudServer, self)._ChatBot__fetch_share_tokeninfo(access_token)  # noqa
                    payload = {'exp': ti['expire_at']}

                resp = jsonify({'code': 0, 'url': next_url if next_url else '/'})
                super(MyCloudServer, self)._ChatBot__set_cookie(resp, access_token, payload['exp'])  # noqa

                return resp
            except Exception as e:
                error = str(e)

        return jsonify({'code': 500, 'message': 'Invalid access token: {}'.format(error)})

    async def generate_share_token(self, unique_name):
        url = MyCloudServer._ChatBot__get_api_prefix() + '/token/register'  # noqa

        async with httpx.AsyncClient(proxies=self.proxy, timeout=30) as client:
            response = await client.post(url, data={
                'unique_name': unique_name,
                'access_token': get_access_token(self.refresh_token),
            })
            if response.status_code == 404:
                raise Exception('share token not found or expired')

            if response.status_code != 200:
                raise Exception(
                    'failed to fetch share token info')

        return response.json()['token_key']

    def run(self, bind_str, threads=8, listen=True):
        app = super().run(bind_str, listen=False)
        resource_path = abspath(join(dirname(__file__), 'flask'))
        # app.static_folder = join(resource_path, 'static')
        app.template_folder = join(resource_path, 'templates')
        host, port = super(MyCloudServer, self)._ChatBot__parse_bind(bind_str)  # noqa
        if listen:
            serve(app, host=host, port=port, ident=None, threads=threads)
        return app


class MyChatGPT(ChatGPT):
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
        access_tokens = {'default': get_access_token(self.refresh_token)}
        super().__init__(access_tokens)

    def get_access_token(self, token_key=None):
        access_token = super().get_access_token(token_key)
        if not access_token or not check_access_token_out(access_token):
            access_token = get_access_token(self.refresh_token)
            self.access_tokens[token_key or self.default_token_key] = access_token
        return access_token

# ChatBotServer(MyChatGPT(refresh_token), True).run(bind_url)
 app = MyCloudServer(os.getenv('REFRESH_TOKEN')).run(os.getenv('SERVER', '0.0.0.0:8018'), listen=False)
