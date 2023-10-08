from flask import Flask, request, Response, make_response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, origins=["*"])

# 目标站点的URL
PREFIX = "https://ai.fakeopen.com"

es_paths = [
    "api/conversation",
]


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def reverse_proxy(path):
    method = request.method
    target_url = f"{PREFIX}/{path}"
    args = request.args
    headers = {key: value for key, value in request.headers if key != 'Host'}
    data = request.get_data()
    if path in es_paths:
        # 事件流
        def stream():
            try:
                res = requests.request(
                    method,
                    target_url,
                    headers=headers,
                    params=args,
                    data=data,
                    proxies={'all': "http://127.0.0.1:1080"},
                    stream=True,
                )
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

        return Response(stream(), content_type='text/event-stream')
    else:
        # 普通请求
        response = requests.request(
            method,
            target_url,
            headers=headers,
            params=args,
            data=data,
            proxies={'all': "http://127.0.0.1:1080"},
        )
        resp = make_response(response.content)
        resp.status_code = response.status_code
        # for key, value in response.headers.items():
        #     resp.headers[key] = value
        return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
