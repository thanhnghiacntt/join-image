#!/usr/bin/env python3
"""
Ghép nhiều ảnh (ảnh vệ tinh / ảnh chụp màn hình bản đồ / ảnh scan) thành 1 ảnh lớn.

- Ảnh đầu tiên là ảnh chuẩn (giữ nguyên hệ toạ độ, không bị biến dạng).
- Các ảnh sau: tìm điểm đặc trưng (SIFT) khớp với phần ảnh đã ghép, ước lượng
  phép biến đổi rồi đặt vào đúng vị trí. Ảnh chưa khớp được sẽ được thử lại
  sau khi các ảnh khác đã ghép xong (không cần nhập đúng thứ tự).
- Canvas tự mở rộng; chỗ không có ảnh nào thì trong suốt (PNG RGBA).

Cách dùng:
    python stitch.py thu_muc_anh                 # quét thư mục, ảnh tạo sớm nhất làm chuẩn
    python stitch.py thu_muc_anh -r -o out.png   # quét cả thư mục con
    python stitch.py 1.png 2.png 3.png -o ket_qua.png
    python stitch.py thu_muc_anh/*.png -o out.png --model homography --blend feather

Yêu cầu: pip install opencv-python numpy
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


# ---------------------------------------------------------------- tiện ích
def load_rgba(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(path)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img


def make_detector(n_features):
    if hasattr(cv2, "SIFT_create"):
        return cv2.SIFT_create(nfeatures=n_features), cv2.NORM_L2
    return cv2.ORB_create(nfeatures=n_features), cv2.NORM_HAMMING


def detect(detector, img_bgra, max_side):
    """Tìm keypoint trên ảnh thu nhỏ (cho nhanh), trả toạ độ ở kích thước gốc."""
    h, w = img_bgra.shape[:2]
    s = min(1.0, max_side / max(h, w))
    gray = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2GRAY)
    mask = (img_bgra[:, :, 3] > 0).astype(np.uint8) * 255
    if s < 1.0:
        gray = cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        mask = cv2.resize(mask, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
    mask = cv2.erode(mask, np.ones((5, 5), np.uint8))  # bỏ keypoint sát mép trong suốt
    kps, desc = detector.detectAndCompute(gray, mask)
    pts = np.float32([k.pt for k in kps]) / s if kps else np.empty((0, 2), np.float32)
    return pts, desc


def match(desc_a, desc_b, norm, ratio):
    if desc_a is None or desc_b is None or len(desc_a) < 2 or len(desc_b) < 2:
        return []
    if norm == cv2.NORM_L2:
        matcher = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=64))
    else:
        matcher = cv2.BFMatcher(norm)
    good = []
    for pair in matcher.knnMatch(desc_a, desc_b, k=2):
        if len(pair) == 2 and pair[0].distance < ratio * pair[1].distance:
            good.append(pair[0])
    return good


def estimate(src, dst, model, thresh):
    """Trả ma trận 3x3 biến src -> dst và số inlier."""
    if model == "translation":
        # RANSAC đơn giản trên vector dịch chuyển
        d = dst - src
        best, best_in = None, None
        rng = np.random.default_rng(0)
        for i in rng.integers(0, len(d), min(500, len(d))):
            inl = np.linalg.norm(d - d[i], axis=1) < thresh
            if best_in is None or inl.sum() > best_in.sum():
                best, best_in = d[i], inl
        t = d[best_in].mean(axis=0)
        H = np.array([[1, 0, t[0]], [0, 1, t[1]], [0, 0, 1]], np.float64)
        return H, int(best_in.sum())
    if model == "homography":
        H, inl = cv2.findHomography(src, dst, cv2.RANSAC, thresh)
    else:  # similarity: xoay + tỉ lệ + dịch, không méo -> ít trôi lệch nhất
        A, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC,
                                             ransacReprojThreshold=thresh)
        H = None if A is None else np.vstack([A, [0, 0, 1]])
    if H is None:
        return None, 0
    return H, int(inl.sum())


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, base):
        self.img = base.copy()          # BGRA uint8
        self.ox, self.oy = 0, 0         # vị trí gốc (0,0) của ảnh chuẩn trong canvas

    def expand_for(self, H, w, h):
        """Mở rộng canvas để chứa ảnh kích thước w×h sau khi biến đổi bởi H
        (H tính theo hệ toạ độ ảnh chuẩn)."""
        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        c = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
        c[:, 0] += self.ox
        c[:, 1] += self.oy
        ch, cw = self.img.shape[:2]
        left = int(max(0, np.ceil(-c[:, 0].min())))
        top = int(max(0, np.ceil(-c[:, 1].min())))
        right = int(max(0, np.ceil(c[:, 0].max() - cw)))
        bottom = int(max(0, np.ceil(c[:, 1].max() - ch)))
        if left or top or right or bottom:
            self.img = cv2.copyMakeBorder(self.img, top, bottom, left, right,
                                          cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
            self.ox += left
            self.oy += top

    def paste(self, img, H, blend):
        h, w = img.shape[:2]
        self.expand_for(H, w, h)
        T = np.array([[1, 0, self.ox], [0, 1, self.oy], [0, 0, 1]], np.float64)
        ch, cw = self.img.shape[:2]
        warped = cv2.warpPerspective(img, T @ H, (cw, ch), flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        new_a = warped[:, :, 3] > 127
        old_a = self.img[:, :, 3] > 0
        only_new = new_a & ~old_a

        # Chỗ chưa có gì: lấy ảnh mới
        self.img[only_new] = warped[only_new]
        self.img[only_new, 3] = 255

        if blend == "feather":
            both = new_a & old_a
            if both.any():
                # trọng số theo khoảng cách tới mép của mỗi ảnh -> chuyển tiếp mượt
                d_old = cv2.distanceTransform(old_a.astype(np.uint8), cv2.DIST_L2, 3)
                d_new = cv2.distanceTransform(new_a.astype(np.uint8), cv2.DIST_L2, 3)
                wgt = (d_new / (d_old + d_new + 1e-6))[both][:, None]
                self.img[both, :3] = (self.img[both, :3] * (1 - wgt)
                                      + warped[both, :3] * wgt).astype(np.uint8)
        # blend == "keep": vùng giao nhau giữ nguyên ảnh đã có (ảnh trước ưu tiên)


# ---------------------------------------------------------------- quét thư mục
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def creation_time(path):
    """Thời gian tạo file.
    Windows / macOS: thời gian tạo thật (st_birthtime, hoặc st_ctime trên Windows).
    Linux: thường không có thời gian tạo -> dùng thời gian sửa (st_mtime)."""
    st = os.stat(path)
    bt = getattr(st, "st_birthtime", None)
    if bt:
        return bt
    if sys.platform.startswith("win"):
        return st.st_ctime
    return st.st_mtime


def scan_folder(folder, recursive=False, exclude=()):
    exclude = {os.path.abspath(p) for p in exclude}
    pattern = "**/*" if recursive else "*"
    files = [str(p) for p in Path(folder).glob(pattern)
             if p.is_file() and p.suffix.lower() in IMAGE_EXTS
             and os.path.abspath(p) not in exclude]
    # sắp xếp theo thời gian tạo, cũ nhất trước (trùng thời gian thì theo tên)
    files.sort(key=lambda p: (creation_time(p), p))
    return files


# ---------------------------------------------------------------- main
def stitch(paths, model="similarity", blend="keep", max_side=2000,
           n_features=8000, ratio=0.75, min_inliers=25, thresh=4.0, verbose=True):
    detector, norm = make_detector(n_features)
    log = print if verbose else (lambda *a, **k: None)

    images = [load_rgba(p) for p in paths]
    feats = [detect(detector, im, max_side) for im in images]

    canvas = Canvas(images[0])
    # Tập điểm đặc trưng "đã ghép", toạ độ theo hệ ảnh chuẩn
    ref_pts, ref_desc = feats[0]
    pending = list(range(1, len(images)))
    log(f"[0] {paths[0]}: ảnh chuẩn, {len(ref_pts)} điểm đặc trưng")

    progress = True
    while pending and progress:
        progress = False
        for i in list(pending):
            pts, desc = feats[i]
            good = match(desc, ref_desc, norm, ratio)
            if len(good) < min_inliers:
                continue
            src = pts[[m.queryIdx for m in good]]
            dst = ref_pts[[m.trainIdx for m in good]]
            H, n_in = estimate(src, dst, model, thresh)
            if H is None or n_in < min_inliers:
                continue
            canvas.paste(images[i], H, blend)
            # thêm điểm đặc trưng của ảnh này (đã chuyển về hệ chuẩn) để ảnh sau có thể khớp
            pts_ref = cv2.perspectiveTransform(pts.reshape(-1, 1, 2).astype(np.float64), H)
            ref_pts = np.vstack([ref_pts, pts_ref.reshape(-1, 2).astype(np.float32)])
            ref_desc = np.vstack([ref_desc, desc])
            log(f"[{i}] {paths[i]}: ghép OK ({n_in}/{len(good)} inlier)")
            pending.remove(i)
            progress = True

    for i in pending:
        log(f"[{i}] {paths[i]}: KHÔNG tìm thấy phần giao nhau -> bỏ qua", file=sys.stderr)

    # cắt bỏ viền trong suốt thừa
    a = canvas.img[:, :, 3]
    ys, xs = np.nonzero(a)
    return canvas.img[ys.min():ys.max() + 1, xs.min():xs.max() + 1], pending


def main():
    ap = argparse.ArgumentParser(description="Ghép nhiều ảnh thành 1 ảnh lớn (nền trong suốt)")
    ap.add_argument("inputs", nargs="+",
                    help="thư mục chứa ảnh (ảnh tạo sớm nhất là ảnh chuẩn), "
                         "hoặc danh sách file ảnh (file đầu tiên là ảnh chuẩn)")
    ap.add_argument("-o", "--output", default=None,
                    help="file PNG đầu ra (mặc định: <thư mục>/stitched.png hoặc ./stitched.png)")
    ap.add_argument("-r", "--recursive", action="store_true", help="quét cả thư mục con")
    ap.add_argument("--model", choices=["translation", "similarity", "homography"],
                    default="similarity",
                    help="translation: chỉ dịch chuyển; similarity (mặc định): dịch+xoay+tỉ lệ; "
                         "homography: phối cảnh đầy đủ")
    ap.add_argument("--blend", choices=["keep", "feather"], default="keep",
                    help="keep: vùng giao giữ ảnh trước; feather: trộn mượt")
    ap.add_argument("--max-side", type=int, default=2000,
                    help="cạnh lớn nhất khi dò đặc trưng (giảm cho nhanh)")
    ap.add_argument("--min-inliers", type=int, default=25)
    args = ap.parse_args()

    if len(args.inputs) == 1 and os.path.isdir(args.inputs[0]):
        folder = args.inputs[0]
        output = args.output or os.path.join(folder, "stitched.png")
        images = scan_folder(folder, args.recursive,
                             exclude=[output, os.path.join(folder, "stitched.png")])
        print(f"Quét {folder}: tìm thấy {len(images)} ảnh (theo thời gian tạo, cũ nhất trước)")
        for i, p in enumerate(images):
            t = datetime.fromtimestamp(creation_time(p)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {i:>3}. {t}  {os.path.relpath(p, folder)}" + ("  <- ảnh chuẩn" if i == 0 else ""))
    else:
        images = args.inputs
        output = args.output or "stitched.png"

    if not images:
        ap.error("không tìm thấy ảnh nào")
    out, failed = stitch(images, args.model, args.blend, args.max_side,
                         min_inliers=args.min_inliers)
    args.output = output
    cv2.imwrite(args.output, out)
    print(f"Đã lưu {args.output} ({out.shape[1]}×{out.shape[0]})"
          + (f", {len(failed)} ảnh không ghép được" if failed else ""))


if __name__ == "__main__":
    main()
