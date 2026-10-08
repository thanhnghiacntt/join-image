# Hướng dẫn sử dụng công cụ ghép ảnh (stitch.py)

Công cụ này ghép nhiều ảnh có phần chồng lên nhau (ảnh vệ tinh, ảnh chụp màn hình bản đồ, ảnh scan) thành một ảnh lớn. Kết quả là file PNG, chỗ nào không có ảnh thì để **trong suốt**.

- **Ảnh chuẩn** là ảnh có **thời gian tạo cũ nhất** trong thư mục. Ảnh này giữ nguyên, không bị xoay hay méo.
- Các ảnh còn lại được dò phần giao nhau rồi tự xoay hoặc co giãn để khớp vào. Bạn không cần sắp xếp ảnh theo thứ tự.

Thư mục công cụ gồm:
```
ghep-anh/
├── stitch.py          # chương trình chính
├── nir.py             # tạo band pseudo-NIR từ GeoTIFF RGB (xem Phần G)
├── requirements.txt   # danh sách thư viện (numpy, opencv-python-headless)
├── install.bat / install.sh   # (tuỳ chọn) script cài tự động
├── stitch.bat  / stitch.sh    # (tuỳ chọn) script chạy nhanh
└── HUONG_DAN.md
```

---

## Phần A — Windows

### A1. Cài Python (chỉ làm 1 lần)
1. Tải Python 3.9 trở lên tại https://www.python.org/downloads/
2. Khi cài, **tick ô "Add python.exe to PATH"**.
3. Mở **Command Prompt** (cmd) rồi kiểm tra:
   ```bat
   python --version
   ```

### A2. Tạo môi trường ảo riêng và cài thư viện (chỉ làm 1 lần)
Giả sử bạn giải nén công cụ vào `D:\tools\ghep-anh`.

```bat
cd /d D:\tools\ghep-anh

:: 1. Tạo môi trường ảo tên .venv ngay trong thư mục công cụ
python -m venv .venv

:: 2. Kích hoạt môi trường ảo
.venv\Scripts\activate

:: 3. Cài thư viện vào môi trường ảo
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. Kiểm tra
python -c "import cv2, numpy; print('OpenCV', cv2.__version__, '| NumPy', numpy.__version__)"
```

Sau bước 2, đầu dòng lệnh sẽ có chữ `(.venv)`, ví dụ `(.venv) D:\tools\ghep-anh>`. Chữ này cho biết bạn **đang ở trong môi trường ảo**, và mọi lệnh `python` hoặc `pip` lúc này chỉ tác động vào `.venv`, không ảnh hưởng Python của máy.

> **Nếu dùng PowerShell** thay cho cmd, lệnh kích hoạt là:
> ```powershell
> .venv\Scripts\Activate.ps1
> ```
> Nếu bị báo lỗi *"running scripts is disabled on this system"*, hãy chạy lệnh sau **một lần**, rồi kích hoạt lại:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### A3. Chạy ghép ảnh (mỗi lần sử dụng)
```bat
cd /d D:\tools\ghep-anh
.venv\Scripts\activate

python stitch.py D:\anh_ve_tinh
```
Kết quả được lưu ở `D:\anh_ve_tinh\stitched.png`.

Dùng xong, thoát môi trường ảo bằng lệnh:
```bat
deactivate
```

**Chạy mà không cần kích hoạt:** gọi thẳng Python trong `.venv`. Lệnh này chạy được từ bất kỳ thư mục nào.
```bat
D:\tools\ghep-anh\.venv\Scripts\python.exe D:\tools\ghep-anh\stitch.py D:\anh_ve_tinh
```

---

## Phần B — Ubuntu / Linux

### B1. Cài Python và venv (chỉ làm 1 lần)
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

### B2. Tạo môi trường ảo riêng và cài thư viện (chỉ làm 1 lần)
Giả sử công cụ nằm ở `~/tools/ghep-anh`.

```bash
cd ~/tools/ghep-anh

# 1. Tạo môi trường ảo tên .venv
python3 -m venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Cài thư viện vào môi trường ảo
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Kiểm tra
python -c "import cv2, numpy; print('OpenCV', cv2.__version__, '| NumPy', numpy.__version__)"
```

Sau bước 2, đầu dòng lệnh sẽ có `(.venv)`. Từ đây bạn dùng `python` và `pip`, không cần gõ `python3` hay `pip3` nữa.

> Không cần `sudo` khi `pip install` trong môi trường ảo. Nếu thấy lỗi *"externally-managed-environment"*, nghĩa là bạn **chưa kích hoạt** môi trường ảo: hãy chạy lại lệnh `source .venv/bin/activate`.

### B3. Chạy ghép ảnh (mỗi lần sử dụng)
```bash
cd ~/tools/ghep-anh
source .venv/bin/activate

python stitch.py ~/anh_ve_tinh
```
Kết quả được lưu ở `~/anh_ve_tinh/stitched.png`.

Dùng xong, thoát môi trường ảo bằng lệnh:
```bash
deactivate
```

**Chạy mà không cần kích hoạt:**
```bash
~/tools/ghep-anh/.venv/bin/python ~/tools/ghep-anh/stitch.py ~/anh_ve_tinh
```

**(Tuỳ chọn) Tạo lệnh tắt `ghepanh`** để gõ được ở bất kỳ thư mục nào:
```bash
echo "alias ghepanh='~/tools/ghep-anh/.venv/bin/python ~/tools/ghep-anh/stitch.py'" >> ~/.bashrc
source ~/.bashrc

ghepanh ~/anh_ve_tinh
```

---

## Phần C — Cách tự động (không bắt buộc)

Nếu không muốn gõ các lệnh ở phần A2 và B2, bạn có thể dùng script có sẵn. Script làm đúng các bước tạo `.venv` và cài thư viện như trên.

| | Cài đặt (1 lần) | Chạy |
|---|---|---|
| Windows | nhấp đúp `install.bat` | `stitch.bat D:\anh_ve_tinh`, hoặc **kéo thả thư mục ảnh vào `stitch.bat`** |
| Ubuntu | `chmod +x *.sh && ./install.sh` | `./stitch.sh ~/anh_ve_tinh` |

`stitch.bat` và `stitch.sh` tự dùng Python trong `.venv`, nên không cần kích hoạt.

---

## Phần D — Cú pháp lệnh và tuỳ chọn

```
python stitch.py <thư_mục_ảnh> [tuỳ chọn]
python stitch.py <ảnh1> <ảnh2> ... [tuỳ chọn]     # file đầu tiên là ảnh chuẩn
```

| Tuỳ chọn | Ý nghĩa | Mặc định |
|---|---|---|
| `-o FILE` | Đường dẫn file kết quả | `<thư mục>/stitched.png` |
| `-r` | Quét cả các thư mục con | không quét |
| `--model translation` | Chỉ dịch chuyển. Phù hợp ảnh chụp màn hình cùng mức zoom, không xoay | |
| `--model similarity` | Dịch, xoay và co giãn. Phù hợp hầu hết ảnh vệ tinh hoặc bản đồ | ✔ |
| `--model homography` | Phối cảnh đầy đủ. Dùng cho ảnh chụp nghiêng hoặc ảnh scan bị méo | |
| `--blend keep` | Ở vùng chồng nhau thì giữ ảnh đã ghép trước | ✔ |
| `--blend feather` | Trộn mượt vùng chồng nhau, ít thấy đường nối hơn | |
| `--max-side N` | Kích thước tối đa dùng khi dò đặc trưng. Giảm để chạy nhanh hơn, tăng để chính xác hơn | 2000 |
| `--min-inliers N` | Số điểm khớp tối thiểu để chấp nhận ghép một ảnh | 25 |
| `-h` | Xem trợ giúp | |

Ví dụ (đã kích hoạt `.venv`):
```bash
python stitch.py D:\anh_ve_tinh -o D:\ket_qua\ban_do.png --blend feather
python stitch.py ~/du_an -r --model homography
python stitch.py 1.png 2.png 3.png -o out.png
```

Ví dụ màn hình khi chạy:
```
Quét D:\anh_ve_tinh: tìm thấy 3 ảnh (theo thời gian tạo, cũ nhất trước)
    0. 2026-10-05 21:50:12  1.png  <- ảnh chuẩn
    1. 2026-10-05 21:51:03  2.png
    2. 2026-10-05 21:52:40  3.png
[0] ...1.png: ảnh chuẩn, 8000 điểm đặc trưng
[1] ...2.png: ghép OK (410/2525 inlier)
[2] ...3.png: ghép OK (122/502 inlier)
Đã lưu D:\anh_ve_tinh\stitched.png (3607×1345)
```

---

## Phần E — Lưu ý

- **Định dạng ảnh được nhận:** png, jpg, jpeg, tif, tiff, bmp, webp. File `stitched.png` cũ trong thư mục sẽ không bị quét lại.
- **Thời gian tạo file:**
  - Windows dùng thời gian tạo thật.
  - Ubuntu dùng thời gian sửa đổi, vì hệ thống thường không cung cấp thời gian tạo.
  - Copy hoặc giải nén có thể làm đổi thời gian này. Nếu ảnh chuẩn bị chọn sai, hãy truyền danh sách file theo thứ tự mong muốn.
- **Mỗi ảnh nên chồng lên ít nhất ~20–30% với một ảnh khác.** Ảnh không tìm thấy phần giao sẽ bị bỏ qua và in cảnh báo `KHÔNG tìm thấy phần giao nhau`.
- **Khi chụp ảnh bản đồ hoặc vệ tinh:** giữ cùng mức zoom, chờ ảnh tải xong mới chụp, và tắt nhãn hoặc icon nếu có thể.
- **Ghép rất nhiều ảnh lớn** sẽ tốn RAM. Khi đó nên ghép theo cụm rồi ghép các cụm lại với nhau.
- **Gỡ cài đặt:** xoá thư mục `ghep-anh`. **Cài lại từ đầu:** xoá thư mục `.venv` rồi làm lại bước A2 hoặc B2.
- **Không di chuyển hoặc đổi tên thư mục chứa `.venv`** sau khi tạo, vì môi trường ảo sẽ hỏng. Nếu đã lỡ làm, hãy xoá `.venv` rồi tạo lại.

## Phần F — Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `'python' is not recognized...` (Windows) | Cài lại Python và tick "Add to PATH", hoặc dùng `py` thay cho `python` |
| `running scripts is disabled` (PowerShell) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `No module named venv` / `ensurepip is not available` (Ubuntu) | `sudo apt install python3-venv` |
| `externally-managed-environment` (Ubuntu) | Chưa kích hoạt `.venv`: chạy `source .venv/bin/activate` |
| `ModuleNotFoundError: No module named 'cv2'` | Chưa kích hoạt `.venv`, hoặc chưa chạy `pip install -r requirements.txt` |
| `libGL.so.1: cannot open shared object` (Ubuntu) | Lỗi này xảy ra khi bạn cài `opencv-python` thay cho bản headless. Chạy `pip uninstall opencv-python` rồi `pip install opencv-python-headless` |
| Ảnh bị ghép lệch hoặc méo | Thử `--model translation`, hoặc `--min-inliers 50` |
| Một số ảnh bị bỏ qua | Thử `--max-side 3000`, hoặc kiểm tra lại phần chồng giữa các ảnh |

---

## Phần G — Tạo band pseudo-NIR từ GeoTIFF (nir.py)

`nir.py` đọc một file GeoTIFF **RGB hoặc RGBA** và ghi ra GeoTIFF mới có **4 band**. Band thứ 4 là NIR (cận hồng ngoại) giả lập, tính từ Red và Green.

| Band | Nội dung |
|---|---|
| 1 | Red |
| 2 | Green |
| 3 | Blue |
| 4 | Pseudo-NIR |

**Công thức:** `NIR = G + (G - R) = 2*G - R`

Đây chỉ là giá trị ước lượng từ ảnh màu thường, không phải dữ liệu NIR thật từ cảm biến.

### G1. Cài thư viện
`nir.py` cần thêm `rasterio`, thư viện này chưa có trong `requirements.txt`. Kích hoạt `.venv` rồi cài:
```bash
pip install rasterio
```

### G2. Cú pháp
```
python nir.py -i <file_vào.tif> -o <file_ra.tif>
```

| Tuỳ chọn | Ý nghĩa | Bắt buộc |
|---|---|---|
| `-i`, `--input` | GeoTIFF RGB hoặc RGBA đầu vào | ✔ |
| `-o`, `--output` | GeoTIFF RGB+NIR đầu ra | ✔ |
| `-h` | Xem trợ giúp | |

Ví dụ:
```bash
python nir.py -i stitched_georef.tif -o stitched_nir.tif
python nir.py --input D:\anh\input.tif --output D:\anh\output_nir.tif
```

### G3. Lưu ý
- File đầu vào phải có **ít nhất 3 band**. Nếu ít hơn, chương trình báo lỗi.
- File đầu ra giữ nguyên kích thước, hệ toạ độ (CRS), kiểu dữ liệu và thông tin địa lý của file gốc. Kết quả nén bằng LZW.
- **Vùng trong suốt** (alpha = 0 hoặc trùng giá trị nodata) được giữ trong suốt ở cả 4 band. Nếu file gốc có alpha mà không có nodata, nodata của file ra là `0`.
- Giá trị NIR vượt miền của kiểu dữ liệu được cắt về giới hạn. Ví dụ ảnh 8-bit bị giới hạn trong 0–255.
- Chương trình xử lý theo từng khối (block), nên ảnh lớn không cần nạp hết vào RAM.
- Nếu muốn có hệ toạ độ, hãy dùng ảnh GeoTIFF đã được gán toạ độ (georeferenced). Ảnh `stitched.png` từ `stitch.py` không có thông tin này.
