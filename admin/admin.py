"""
博客后台管理服务（本地运行，只监听 127.0.0.1）。

    python admin.py

然后浏览器打开 http://127.0.0.1:8910/

职责：
  · 读取 / 保存 admin/content.json（内容主库）
  · 调用 build.py 一键重建静态站
它不做鉴权，因为只绑本机回环地址，别改 HOST 往外暴露。
"""

import base64
import json
import mimetypes
import os
import subprocess
import sys
import re
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import build as builder

ADMIN_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(ADMIN_DIR, 'ui')
HOST = '127.0.0.1'
PORT = 8910

_lock = threading.Lock()
_job = {'running': False, 'log': [], 'done': False, 'ok': False, 'started': 0}


# ---------------------------------------------------------------- 重建任务

def _run_rebuild():
    global _job
    with _lock:
        _job = {'running': True, 'log': [], 'done': False, 'ok': False, 'started': time.time()}
    try:
        # 用独立进程跑构建，而不是在服务进程里跑：
        # 长驻进程持有某些文件句柄时，写 mock-data.ts 会 PermissionError；
        # 独立进程与手动执行 `python build.py --rebuild` 完全同一条路径。
        proc = subprocess.Popen(
            [sys.executable, os.path.join(ADMIN_DIR, 'build.py'), '--rebuild'],
            cwd=ADMIN_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            with _lock:
                _job['log'].append(line.rstrip())
        code = proc.wait()
        if code != 0:
            raise RuntimeError('构建进程退出码 %d' % code)
        with _lock:
            _job['ok'] = True
    except Exception:
        with _lock:
            _job['log'].append('✗ 出错：')
            for line in traceback.format_exc().splitlines():
                _job['log'].append('   ' + line)
    finally:
        with _lock:
            _job['running'] = False
            _job['done'] = True


# ---------------------------------------------------------------- 请求处理

class Handler(BaseHTTPRequestHandler):
    server_version = 'iielxy-admin/1.0'

    # ---- 工具方法
    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get('Content-Length') or 0)
        if length <= 0:
            return None
        return json.loads(self.rfile.read(length).decode('utf-8'))

    def _serve_file(self, path):
        if not os.path.isfile(path):
            self.send_error(404, 'Not Found')
            return
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        if path.endswith(('.html', '.js', '.css')):
            ctype += '; charset=utf-8'
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    # ---- 路由
    def do_GET(self):
        path = self.path.split('?')[0]

        if path in ('/', '/index.html'):
            return self._serve_file(os.path.join(UI_DIR, 'index.html'))

        if path == '/api/content':
            try:
                return self._json({'ok': True, 'content': builder.load_content()})
            except Exception as e:
                return self._json({'ok': False, 'error': str(e)}, 500)

        if path == '/api/status':
            # 内容库比线上成品新 → 说明有改动还没发布
            index = os.path.join(builder.SITE_DIR, 'index.html')
            content_mtime = os.path.getmtime(builder.CONTENT_FILE) if os.path.isfile(builder.CONTENT_FILE) else 0
            site_mtime = os.path.getmtime(index) if os.path.isfile(index) else 0
            return self._json({
                'ok': True,
                'pending': content_mtime > site_mtime,
                'publishedAt': time.strftime('%m-%d %H:%M', time.localtime(site_mtime)) if site_mtime else '',
            })

        if path == '/api/rebuild':
            with _lock:
                snap = dict(_job)
                snap['log'] = list(_job['log'])
            return self._json({'ok': True, 'job': snap})

        # 站点图片直接读构建目录的 public，方便后台预览头像/证书
        if path.startswith('/img/') or path.startswith('/covers/') or path.startswith('/awards/'):
            rel = path.lstrip('/').split('?')[0]
            base = os.path.normpath(os.path.join(builder.BUILD_DIR, 'public'))
            target = os.path.normpath(os.path.join(base, *rel.split('/')))
            if not target.startswith(base):
                return self.send_error(403, 'Forbidden')
            return self._serve_file(target)

        # 其余当静态文件（ui/ 下）
        safe = os.path.normpath(path.lstrip('/'))
        if safe.startswith('..'):
            return self.send_error(403, 'Forbidden')
        return self._serve_file(os.path.join(UI_DIR, safe))

    def do_POST(self):
        path = self.path.split('?')[0]

        if path == '/api/content':
            try:
                payload = self._read_json()
                content = (payload or {}).get('content')
                if not isinstance(content, dict) or 'posts' not in content:
                    return self._json({'ok': False, 'error': '内容结构不合法'}, 400)

                # 保存前留一份备份
                if os.path.isfile(builder.CONTENT_FILE):
                    with open(builder.CONTENT_FILE, encoding='utf-8') as f:
                        backup = f.read()
                    with open(builder.CONTENT_FILE + '.bak', 'w', encoding='utf-8') as f:
                        f.write(backup)

                builder.save_content(content)
                if not _job['running']:
                    builder.write_mock_data(content)
                    builder.write_about(content)
                return self._json({'ok': True, 'savedAt': time.strftime('%H:%M:%S')})
            except Exception as e:
                return self._json({'ok': False, 'error': str(e)}, 500)

        if path == '/api/rebuild':
            with _lock:
                if _job['running']:
                    return self._json({'ok': False, 'error': '正在构建中，请稍候'}, 409)
            threading.Thread(target=_run_rebuild, daemon=True).start()
            return self._json({'ok': True})

        if path == '/api/upload':
            try:
                payload = self._read_json() or {}
                data_url = payload.get('dataUrl') or ''
                name = re.sub(r'[^a-z0-9_-]', '', str(payload.get('name') or 'image').lower()) or 'image'

                m = re.match(r'^data:image/(png|jpeg|jpg|webp|gif|svg\+xml);base64,(.+)$', data_url, re.S)
                if not m:
                    return self._json({'ok': False, 'error': '只支持 png / jpg / webp / gif / svg'}, 400)

                kind, b64 = m.group(1), m.group(2)
                ext = {'jpeg': 'jpg', 'svg+xml': 'svg'}.get(kind, kind)
                raw = base64.b64decode(b64)
                if len(raw) > 8 * 1024 * 1024:
                    return self._json({'ok': False, 'error': '图片超过 8MB，请先压缩'}, 400)

                target_dir = os.path.join(builder.ROOT, 'simpletheme-build', 'public', 'img')
                os.makedirs(target_dir, exist_ok=True)
                filename = '%s.%s' % (name, ext)
                with open(os.path.join(target_dir, filename), 'wb') as f:
                    f.write(raw)

                # 带上时间戳，避免浏览器拿缓存里的旧头像
                url_path = '/img/%s?v=%d' % (filename, int(time.time()))
                return self._json({'ok': True, 'path': url_path, 'bytes': len(raw)})
            except Exception as e:
                return self._json({'ok': False, 'error': str(e)}, 500)

        if path == '/api/restore':
            try:
                bak = builder.CONTENT_FILE + '.bak'
                if not os.path.isfile(bak):
                    return self._json({'ok': False, 'error': '没有可用的备份'}, 404)
                with open(bak, encoding='utf-8') as f:
                    content = json.load(f)
                builder.save_content(content)
                builder.write_mock_data(content)
                return self._json({'ok': True, 'content': content})
            except Exception as e:
                return self._json({'ok': False, 'error': str(e)}, 500)

        self.send_error(404, 'Not Found')

    def log_message(self, fmt, *args):
        # 只打印 API 调用，静态资源不刷屏
        if '/api/' in (args[0] if args else ''):
            print('  %s  %s' % (self.address_string(), fmt % args))


def main():
    if not os.path.isdir(UI_DIR):
        print('找不到界面目录：%s' % UI_DIR)
        return
    url = 'http://%s:%d/' % (HOST, PORT)
    print('=' * 52)
    print('  iielxy 博客后台')
    print('  %s' % url)
    print('  按 Ctrl+C 停止')
    print('=' * 52)
    try:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    except Exception:
        pass
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print('端口 %d 已被占用。' % PORT)
        print('可能是已经开着一个后台窗口了，关掉它再启动，或改本文件顶部的 PORT。')
        input('按回车退出…')
        return
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止。')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
