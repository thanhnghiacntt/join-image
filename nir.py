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

        # Copy metadata từ file gốc
        profile = src.profile.copy()

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

                # ========================================
                # PSEUDO NIR
                #
                # NIR = G + (G - R)
                #     = 2*G - R
                # ========================================

                nir = 2.0 * green - red

                # Xử lý NoData
                if src.nodata is not None:

                    nodata = src.nodata

                    invalid_mask = (
                        (red == nodata)
                        | (green == nodata)
                        | (blue == nodata)
                    )

                    nir[invalid_mask] = nodata

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
    print("Formula:")
    print("NIR = G + (G - R)")
    print("    = 2*G - R")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Tạo pseudo-NIR từ GeoTIFF RGB. "
            "Output gồm 4 band: R, G, B, NIR."
        )
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="File GeoTIFF RGB đầu vào"
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