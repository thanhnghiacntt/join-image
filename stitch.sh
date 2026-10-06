#!/usr/bin/env bash
# Chạy công cụ ghép ảnh bằng môi trường ảo riêng (.venv)
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$HERE/.venv/bin/python" ]; then
    echo "[LỖI] Chưa cài đặt. Hãy chạy ./install.sh trước."
    exit 1
fi
if [ $# -eq 0 ]; then
    exec "$HERE/.venv/bin/python" "$HERE/stitch.py" --help
fi
exec "$HERE/.venv/bin/python" "$HERE/stitch.py" "$@"
