from pandora.bots.server import ChatBot as ChatBotServer

from app import MyChatGPT

if __name__ == '__main__':
    refresh_token = '0wT83njBcpircX0gILNUagl6IIsQCp174JsED4Ji9KY1J'
    bind_url = '127.0.0.1:8080'
    ChatBotServer(MyChatGPT(refresh_token), True).run(bind_url)
