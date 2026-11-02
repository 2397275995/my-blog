"""
本地预览 SimpleTheme 静态站。

用途：直接双击「启动预览.bat」，或命令行运行
    python serve.py

要点：
- 静态站用的是 History 路由（/about、/ji-lu-.../ 这类地址），
  普通静态服务器找不到文件就会 404，所以这里加了 SPA 回退：
  找不到的路径一律返回 index.html，交给前端路由处理。
- Cloudflare Pages 上由产物里的 _redirects 做同样的事。
"""

import http.server
import os
import socketserver
import threading
import urllib.parse
import webbrowser

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simpletheme-static')
PORT = 8904


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def send_head(self):
        path = urllib.parse.urlparse(self.path).path
        fs = self.translate_path(path)
        if os.path.isdir(fs):
            if os.path.exists(os.path.join(fs, 'index.html')):
                return super().send_head()
        if not os.path.exists(fs):
            self.path = '/index.html'
        return super().send_head()

    def do_GET(self):
        # 已安装的 Service Worker 可能缓存旧版本，开发预览时让它失效
        if self.path.endswith('sw.js'):
            self.send_response(404)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        print('  %s - %s' % (self.address_string(), fmt % args))


def main():
    if not os.path.isdir(SITE_DIR):
        print('找不到 site 目录：%s' % SITE_DIR)
        input('按回车退出…')
        return

    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(('127.0.0.1', PORT), SPAHandler)
    except OSError:
        print('端口 %d 已被占用，请先关掉占用的程序，或改本文件里的 PORT。' % PORT)
        input('按回车退出…')
        return

    url = 'http://127.0.0.1:%d/' % PORT
    print('=' * 46)
    print('  SimpleTheme 静态站 · 本地预览')
    print('  %s' % url)
    print('  按 Ctrl+C 停止')
    print('=' * 46)

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止。')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
