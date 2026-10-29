import os
import sys
import urllib.request
import time

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = r"C:\Users\kami\.gemini\antigravity\scratch\free-subtitles-webgpu\model_cache\china\onnx-community\whisper-small\resolve\main"
REMOTE_BASE = "https://hf-mirror.com/onnx-community/whisper-small/resolve/main"

FILES = [
    ("onnx/encoder_model.onnx", os.path.join(BASE_DIR, "onnx", "encoder_model.onnx")),
    ("onnx/decoder_model_merged_q4.onnx", os.path.join(BASE_DIR, "onnx", "decoder_model_merged_q4.onnx"))
]

def download_file(rel_path, local_path):
    url = f"{REMOTE_BASE}/{rel_path}"
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # 检查远程大小
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        remote_size = int(resp.headers.get('Content-Length', 0))

    if os.path.exists(local_path) and os.path.getsize(local_path) == remote_size:
        print(f"✅ 已存在且完整: {rel_path} ({remote_size // (1024*1024)} MB)")
        return

    print(f"📥 开始稳健下载: {rel_path} ({remote_size // (1024*1024)} MB)...")
    tmp_path = local_path + ".downloading"
    
    # 循环重试下载
    for attempt in range(5):
        try:
            req_get = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_get, timeout=60) as resp, open(tmp_path, 'wb') as f:
                downloaded = 0
                last_print = time.time()
                while chunk := resp.read(256 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if time.time() - last_print > 1.0:
                        pct = (downloaded / remote_size) * 100 if remote_size else 0
                        print(f"  -> {rel_path}: {downloaded // (1024*1024)}MB / {remote_size // (1024*1024)}MB ({pct:.1f}%)")
                        last_print = time.time()

            if os.path.getsize(tmp_path) == remote_size:
                if os.path.exists(local_path):
                    os.remove(local_path)
                os.rename(tmp_path, local_path)
                print(f"🎉 下载完成: {rel_path}")
                return
            else:
                print(f"⚠️ 文件不完整，尝试第 {attempt+2} 次...")
        except Exception as e:
            print(f"⚠️ 下载错误 ({e})，3秒后重试第 {attempt+2} 次...")
            time.sleep(3)

    print(f"❌ 下载失败: {rel_path}")

def main():
    print("=" * 60)
    print("🚀 开始后台预载【Whisper Small 高精准度模型】所有权重...")
    print("=" * 60)
    for rel_path, local_path in FILES:
        download_file(rel_path, local_path)
    print("=" * 60)
    print("✅ 全部 Whisper Small 高精准度模型已就绪！")
    print("=" * 60)

if __name__ == '__main__':
    main()
