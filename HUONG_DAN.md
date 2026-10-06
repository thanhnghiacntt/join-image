# Công cụ ghép ảnh (stitch.py)

Công cụ này ghép nhiều ảnh có phần chồng lên nhau (ảnh vệ tinh, ảnh chụp màn hình bản đồ, ảnh scan) thành một ảnh lớn. Kết quả là file PNG, chỗ nào không có ảnh thì để **trong suốt**.

- Ảnh chuẩn là ảnh có **thời gian tạo cũ nhất** trong thư mục. Ảnh này giữ nguyên, không bị xoay hay méo.
- Các ảnh còn lại được dò phần giao nhau rồi tự xoay hoặc co giãn để khớp vào. Bạn không cần đặt tên hay sắp xếp ảnh theo thứ tự.

---

## 1. Yêu cầu

- **Python 3.9 trở lên**
  - Windows: tải tại https://www.python.org/downloads/ và nhớ **tick "Add python.exe to PATH"** khi cài.
  - Ubuntu/Debian: `sudo apt install python3 python3-venv`
  - macOS: `brew install python`
- Cần có mạng ở lần cài đặt đầu tiên (để tải OpenCV và NumPy, khoảng 50 MB).

## 2. Cài đặt (chỉ làm 1 lần)

Giải nén thư mục `ghep-anh` vào chỗ bạn muốn, ví dụ `D:\tools\ghep-anh`.

**Windows:** nhấp đúp vào `install.bat`.

**Linux / macOS:**
```bash
cd ghep-anh
chmod +x install.sh
./install.sh
```

Script cài đặt sẽ tạo **môi trường ảo riêng** là thư mục `.venv` nằm ngay trong `ghep-anh`, rồi cài thư viện vào đó.
- Python hệ thống và các dự án khác **không bị ảnh hưởng**.
- Muốn gỡ hoàn toàn thì chỉ cần xoá thư mục `ghep-anh`.
- Muốn cài lại từ đầu thì xoá thư mục `.venv` rồi chạy lại `install`.

Khi cài thành công, màn hình hiện dòng kiểu `OpenCV 4.x.x | NumPy 2.x.x`.

## 3. Sử dụng

### Cách nhanh nhất (Windows)
**Kéo thả thư mục ảnh vào file `stitch.bat`**. Kết quả được lưu ở `<thư mục ảnh>\stitched.png`.

### Dòng lệnh

| Hệ điều hành | Lệnh |
|---|---|
| Windows (cmd / PowerShell) | `D:\tools\ghep-anh\stitch.bat D:\anh_ve_tinh` |
| Linux / macOS | `./stitch.sh ~/anh_ve_tinh` |

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

### Các tuỳ chọn

| Tuỳ chọn | Ý nghĩa | Mặc định |
|---|---|---|
| `-o FILE` | Đường dẫn file kết quả | `<thư mục>\stitched.png` |
| `-r` | Quét cả các thư mục con | không quét |
| `--model translation` | Chỉ dịch chuyển, phù hợp ảnh chụp màn hình cùng mức zoom và không xoay | |
| `--model similarity` | Dịch, xoay và co giãn. Phù hợp hầu hết ảnh vệ tinh hoặc bản đồ | ✔ |
| `--model homography` | Phối cảnh đầy đủ, dùng cho ảnh chụp nghiêng hoặc ảnh scan bị méo | |
| `--blend keep` | Ở vùng chồng nhau thì giữ ảnh đã ghép trước | ✔ |
| `--blend feather` | Trộn mượt vùng chồng nhau, ít thấy đường nối hơn | |
| `--max-side N` | Kích thước tối đa dùng khi dò đặc trưng. Giảm để chạy nhanh hơn, tăng để chính xác hơn | 2000 |
| `--min-inliers N` | Số điểm khớp tối thiểu để chấp nhận ghép một ảnh | 25 |

Ví dụ:
```bat
stitch.bat D:\anh_ve_tinh -o D:\ket_qua\ban_do.png --blend feather
stitch.bat D:\du_an -r --model homography
stitch.bat 1.png 2.png 3.png -o out.png   (truyền danh sách file: file đầu tiên là ảnh chuẩn)
```

## 4. Lưu ý

- **Định dạng ảnh được nhận:** png, jpg, jpeg, tif, tiff, bmp, webp. File `stitched.png` cũ trong thư mục sẽ không bị quét lại.
- **Thời gian tạo file:**
  - Windows và macOS dùng thời gian tạo thật.
  - Linux dùng thời gian sửa đổi.
  - Copy hoặc giải nén file có thể làm đổi thời gian tạo. Nếu ảnh chuẩn bị chọn sai, hãy truyền danh sách file theo thứ tự mong muốn.
- **Mỗi ảnh nên chồng lên ít nhất ~20–30% với một ảnh khác.** Ảnh không tìm thấy phần giao sẽ bị bỏ qua và in cảnh báo `KHÔNG tìm thấy phần giao nhau`.
- **Mẹo khi chụp ảnh bản đồ hoặc vệ tinh:** giữ cùng mức zoom. Tránh chụp lúc ảnh đang tải dở (bị mờ hoặc thiếu ô). Tắt nhãn, đường và icon nếu có thể, vì chúng trôi theo màn hình và làm giảm độ khớp.
- **Ảnh rất nhiều hoặc rất lớn:** canvas kết quả có thể tốn nhiều RAM. Nên ghép theo từng cụm rồi ghép các cụm lại với nhau.

## 5. Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `Không tìm thấy Python` | Cài Python và tick "Add to PATH", rồi mở lại cửa sổ cmd |
| `Chưa cài đặt. Hãy chạy install...` | Chạy `install.bat` / `install.sh` |
| `Không tạo được venv` (Ubuntu) | `sudo apt install python3-venv` |
| Ảnh bị ghép lệch hoặc méo | Thử `--model translation`, hoặc tăng `--min-inliers 50` |
| Một số ảnh bị bỏ qua | Tăng `--max-side 3000`, hoặc kiểm tra lại phần chồng giữa các ảnh |
