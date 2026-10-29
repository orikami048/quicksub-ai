import http.server
import socketserver
import os
import sys
import shutil
import json
import urllib.request
import urllib.error

# 解决 Windows 特殊编码控制台崩溃 (如 cp932)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

PORT = 8899
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(DIRECTORY, "model_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class DualProxyHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Expose-Headers', 'Content-Length, Content-Range, Accept-Ranges')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        if self.path.startswith('/model-proxy/'):
            parts = self.path[len('/model-proxy/'):].split('/', 1)
            if len(parts) == 2:
                mirror_type, target_subpath = parts
                # 统一共享模型存储池（不分中英文源，同一个模型只存一份，避免翻倍占用）
                safe_local_path = os.path.join(CACHE_DIR, target_subpath.replace('/', os.sep))
                if os.path.exists(safe_local_path):
                    self.send_response(200)
                    self.send_header('Content-Length', str(os.path.getsize(safe_local_path)))
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Accept-Ranges', 'bytes')
                    self.end_headers()
                    return

                upstream_domain = "https://hf-mirror.com" if mirror_type == "china" else "https://huggingface.co"
                target_url = f"{upstream_domain}/{target_subpath}"
                try:
                    req = urllib.request.Request(target_url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        self.send_response(200)
                        self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/octet-stream'))
                        if 'Content-Length' in resp.headers:
                            self.send_header('Content-Length', resp.headers['Content-Length'])
                        self.send_header('Accept-Ranges', 'bytes')
                        self.end_headers()
                        return
                except Exception:
                    self.send_response(200)
                    self.end_headers()
                    return
        super().do_HEAD()

    def do_POST(self):
        if self.path == '/api/clear-cache':
            try:
                if os.path.exists(CACHE_DIR):
                    shutil.rmtree(CACHE_DIR)
                    os.makedirs(CACHE_DIR, exist_ok=True)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"ok","message":"Cache wiped"}')
                print("🧹 [Storage] Local model cache directory wiped successfully.")
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'{{"status":"error","message":"{e}"}}'.encode('utf-8'))
                return
        super().do_POST()

    def do_GET(self):
        # 获取缓存大小 API
        if self.path == '/api/cache-info':
            total_size = 0
            file_count = 0
            if os.path.exists(CACHE_DIR):
                for dirpath, dirnames, filenames in os.walk(CACHE_DIR):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                            file_count += 1
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"sizeBytes": total_size, "files": file_count}).encode('utf-8'))
            return

        # 流式模型反向代理: /model-proxy/{mirror_type}/{path}
        if self.path.startswith('/model-proxy/'):
            parts = self.path[len('/model-proxy/'):].split('/', 1)
            if len(parts) == 2:
                mirror_type, target_subpath = parts
                # 统一共享模型存储池（不分中英文源，同一个模型只存一份，避免翻倍占用）
                safe_local_path = os.path.join(CACHE_DIR, target_subpath.replace('/', os.sep))

                # 1. 命中本地缓存，直接流式返回本地文件
                if os.path.exists(safe_local_path) and os.path.getsize(safe_local_path) > 0:
                    try:
                        file_size = os.path.getsize(safe_local_path)
                        self.send_response(200)
                        self.send_header('Content-Length', str(file_size))
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Accept-Ranges', 'bytes')
                        self.end_headers()
                        with open(safe_local_path, 'rb') as f:
                            while chunk := f.read(256 * 1024):
                                self.wfile.write(chunk)
                        return
                    except Exception as e:
                        print(f"[Cache Serve Error] {e}")

                # 2. 本地无缓存，向上游请求并【一边流式转发给前端，一边写入本地缓存】
                upstream_domain = "https://hf-mirror.com" if mirror_type == "china" else "https://huggingface.co"
                target_url = f"{upstream_domain}/{target_subpath}"
                print(f"📡 [Model Stream Start] {mirror_type.upper()} -> {target_url}")

                tmp_local_path = safe_local_path + ".tmp"
                # 增加最多 3 次失败自动重试机制（抵抗本地安全软件/代理 Reset 连接）
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        req = urllib.request.Request(target_url, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        with urllib.request.urlopen(req, timeout=300) as resp:
                            content_type = resp.headers.get('Content-Type', 'application/octet-stream')
                            content_length = resp.headers.get('Content-Length')

                            self.send_response(200)
                            self.send_header('Content-Type', content_type)
                            if content_length:
                                self.send_header('Content-Length', content_length)
                            self.send_header('Accept-Ranges', 'bytes')
                            self.end_headers()

                            os.makedirs(os.path.dirname(tmp_local_path), exist_ok=True)
                            downloaded_bytes = 0
                            with open(tmp_local_path, 'wb') as tmp_file:
                                while True:
                                    chunk = resp.read(128 * 1024)
                                    if not chunk:
                                        break
                                    tmp_file.write(chunk)
                                    self.wfile.write(chunk)
                                    downloaded_bytes += len(chunk)

                            if content_length and downloaded_bytes < int(content_length):
                                raise RuntimeError(f"Download incomplete ({downloaded_bytes}/{content_length} bytes)")

                            if os.path.exists(safe_local_path):
                                os.remove(safe_local_path)
                            os.rename(tmp_local_path, safe_local_path)
                            print(f"✅ [Stream Done & Cached] {downloaded_bytes // (1024*1024)} MB -> {safe_local_path}")
                            return
                    except Exception as err:
                        print(f"⚠️ [Stream Proxy Attempt {attempt+1}/{max_retries}] {target_url}: {err}")
                        if os.path.exists(tmp_local_path):
                            try: os.remove(tmp_local_path)
                            except: pass
                        if attempt == max_retries - 1:
                            try:
                                self.send_response(502)
                                self.end_headers()
                                self.wfile.write(f"Proxy streaming failed after {max_retries} attempts: {err}".encode('utf-8'))
                            except:
                                pass
                            return

        super().do_GET()

def main():
    os.chdir(DIRECTORY)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    
    port = PORT
    httpd = None
    while port < PORT + 10:
        try:
            httpd = socketserver.ThreadingTCPServer(("0.0.0.0", port), DualProxyHTTPHandler)
            break
        except OSError:
            port += 1

    if not httpd:
        print("Error: Could not bind port.")
        sys.exit(1)

    url = f"http://localhost:{port}/index.html"
    print("=" * 60)
    print(f"[QuickSub AI] Zero-CORS Chunked Streaming Server Started!")
    print(f"URL: {url}")
    print(f"Model Cache: {CACHE_DIR}")
    print("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()

if __name__ == '__main__':
    main()
