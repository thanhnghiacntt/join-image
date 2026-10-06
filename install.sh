#!/usr/bin/env bash
# Cài đặt môi trường ảo riêng (.venv) cho công cụ ghép ảnh — Linux / macOS
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  Cài đặt môi trường cho công cụ ghép ảnh"
echo "============================================"

PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    echo "[LỖI] Không tìm thấy Python 3. Cài bằng: sudo apt install python3 python3-venv  (Ubuntu)"
    echo "      hoặc: brew install python  (macOS)"
    exit 1
fi
"$PY" --version

if [ -x ".venv/bin/python" ]; then
    echo "Môi trường .venv đã tồn tại, bỏ qua bước tạo."
else
    echo "Đang tạo môi trường ảo .venv ..."
    if ! "$PY" -m venv .venv; then
        echo "[LỖI] Không tạo được venv. Trên Ubuntu/Debian hãy cài: sudo apt install python3-venv"
        exit 1
    fi
fi

echo "Đang cài thư viện ..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

.venv/bin/python -c "import cv2, numpy; print('OpenCV', cv2.__version__, '| NumPy', numpy.__version__)"
chmod +x stitch.sh 2>/dev/null || true

echo
echo "Cài đặt xong! Cách dùng:"
echo "  ./stitch.sh /duong/dan/thu_muc_anh"
