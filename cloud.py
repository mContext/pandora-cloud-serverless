import os

from app import MyCloudServer

if __name__ == '__main__':
    refresh_token = '0wT83njBcpircX0gILNUagl6IIsQCp174JsED4Ji9KY1J'
    bind_url = '0.0.0.0:8081'
    os.environ['CHATGPT_API_PREFIX'] = 'http://192.168.60.167:8888'
    MyCloudServer(refresh_token).run(bind_url)
