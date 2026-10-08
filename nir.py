#!/usr/bin/env python3

import argparse
import os

import numpy as np
import rasterio


def clamp_to_dtype(data, dtype):
    """
    Giới hạn giá trị về miền hợp lệ của dtype.
    """
    np_dtype = np.dtype(dtype)

    if np.issubdtype(np_dtype, np.integer):
        info = np.iinfo(np_dtype)
        data = np.clip(data, info.min, info.max)

    return data.astype(np_dtype)


def get_transparency_mask(src, red, green, blue, alpha=None):
    """
    Tạo mask cho các pixel trong suốt.

    Pixel được coi là trong suốt nếu:
    - có giá trị nodata trên ít nhất một band RGB; hoặc
    - band alpha tồn tại và alpha <= 0.
    """
    mask = np.zeros(red.shape, dtype=bool)

    if src.nodata is not None:
        mask |= (red == src.nodata) | (green == src.nodata) | (blue == src.nodata)

    if alpha is not None:
        mask |= alpha <= 0

    return mask


def create_pseudo_nir(input_file, output_file):
    """
    Tạo GeoTIFF 4 band:
        Band 1: Red
        Band 2: Green
        Band 3: Blue
        Band 4: Pseudo NIR

    Công thức:
        NIR = G + (G - R)
            = 2*G - R

    Lưu ý:
        Nếu ảnh đầu vào có vùng trong suốt (alpha = 0 hoặc nodata),
        các pixel đó cũng sẽ được giữ trong suốt ở band NIR bằng cách
        đặt giá trị nodata tương ứng.
    """

    with rasterio.open(input_file) as src:

        if src.count < 3:
            raise ValueError(
                f"File phải có ít nhất 3 band RGB. "
                f"File hiện tại chỉ có {src.count} band."
            )

        print("------------------------------------------")
        print("INPUT")
        print("------------------------------------------")
        print(f"File       : {input_file}")
        print(f"Width      : {src.width}")
        print(f"Height     : {src.height}")
        print(f"Bands      : {src.count}")
        print(f"Data type  : {src.dtypes[0]}")
        print(f"CRS        : {src.crs}")
        print(f"NoData     : {src.nodata}")
        print()

        dtype = src.dtypes[0]
        alpha = src.read(4) if src.count >= 4 else None

        # Copy metadata từ file gốc
        profile = src.profile.copy()

        # Nếu ảnh gốc có alpha hoặc nodata, giữ lại tính trong suốt cho output
        if src.nodata is not None:
            profile["nodata"] = src.nodata
        elif alpha is not None:
            profile["nodata"] = 0

        # Output gồm RGB + NIR
        profile.update(
            count=4,
            compress="lzw",
            BIGTIFF="IF_SAFER"
        )

        with rasterio.open(output_file, "w", **profile) as dst:

            # Xử lý theo từng block/window
            # => không cần load toàn bộ GeoTIFF vào RAM
            for _, window in src.block_windows(1):

                red = src.read(
                    1,
                    window=window
                ).astype(np.float32)

                green = src.read(
                    2,
                    window=window
                ).astype(np.float32)

                blue = src.read(
                    3,
                    window=window
                ).astype(np.float32)

                alpha_block = None
                if alpha is not None:
                    alpha_block = src.read(
                        4,
                        window=window
                    ).astype(np.float32)

                invalid_mask = get_transparency_mask(
                    src=src,
                    red=red,
                    green=green,
                    blue=blue,
                    alpha=alpha_block
                )

                nir = 2.0 * green - red

                nodata_value = src.nodata if src.nodata is not None else 0
                nir[invalid_mask] = nodata_value

                # Giữ nguyên vùng trong suốt ở cả 3 band RGB và band NIR
                red[invalid_mask] = nodata_value
                green[invalid_mask] = nodata_value
                blue[invalid_mask] = nodata_value

                # Giới hạn về đúng datatype gốc
                nir = clamp_to_dtype(
                    nir,
                    dtype
                )

                # Ghi RGB
                dst.write(
                    red.astype(dtype),
                    1,
                    window=window
                )

                dst.write(
                    green.astype(dtype),
                    2,
                    window=window
                )

                dst.write(
                    blue.astype(dtype),
                    3,
                    window=window
                )

                # Ghi NIR vào Band 4
                dst.write(
                    nir,
                    4,
                    window=window
                )

            # Đặt tên band
            dst.set_band_description(
                1,
                "Red"
            )

            dst.set_band_description(
                2,
                "Green"
            )

            dst.set_band_description(
                3,
                "Blue"
            )

            dst.set_band_description(
                4,
                "Pseudo-NIR (2G-R)"
            )

    print("------------------------------------------")
    print("DONE")
    print("------------------------------------------")
    print(f"Output: {output_file}")
    print()
    print("Band 1 : Red")
    print("Band 2 : Green")
    print("Band 3 : Blue")
    print("Band 4 : Pseudo-NIR")
    print()
    print("Công thức:")
    print("NIR = G + (G - R)")
    print("    = 2*G - R")
    print()
    print("Lưu ý:")
    print("- Nếu ảnh đầu vào có vùng trong suốt (alpha = 0 hoặc nodata),")
    print("  phần trong suốt đó cũng sẽ được giữ ở band NIR.")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Tạo pseudo-NIR từ GeoTIFF RGB. "
            "Output gồm 4 band: R, G, B, NIR."
        ),
        epilog=(
            "Ví dụ dùng:\n"
            "  python nir.py -i input.tif -o output_nir.tif\n"
            "  python nir.py --input input.tif --output output_nir.tif\n\n"
            "Nếu ảnh đầu vào có nền trong suốt (alpha = 0 hoặc nodata),\n"
            "vùng đó cũng sẽ được giữ trong suốt ở mặt NIR để khi ghép ảnh\n"
            "không xuất hiện nền trắng/đen lạ."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="File GeoTIFF RGB hoặc RGBA đầu vào"
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="File GeoTIFF RGB+NIR đầu ra"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(
            f"Không tìm thấy file: {args.input}"
        )

    create_pseudo_nir(
        args.input,
        args.output
    )


if __name__ == "__main__":
    main()
