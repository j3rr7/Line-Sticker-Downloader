import httpx
import contextlib


class DownloadManager(contextlib.ContextDecorator):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        self.client = httpx.Client(*self.args, **self.kwargs)
        return self.client

    def __exit__(self, *args):
        self.client.close()
        return False


if __name__ == '__main__':
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
    }
    with DownloadManager() as client:
        response = client.get('https://www.ifconfig.io/ip', headers=headers)
        print(response)
        print(response.text)
        print(response.status_code)
        print(response.content)
        print(response.url)
