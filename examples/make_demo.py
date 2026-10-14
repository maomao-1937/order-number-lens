"""Generate fictional order screenshot for repeatable OCR smoke tests."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("demo.local.png"))
    parser.add_argument("--font", type=Path, help="Optional local font with Chinese glyphs")
    args = parser.parse_args()
    image = Image.new("RGB", (1200, 520), "white")
    draw = ImageDraw.Draw(image)
    if args.font:
        font = ImageFont.truetype(str(args.font), 52)
        label = "订单号: 1234567890123456"
    else:
        font = ImageFont.load_default(size=52)
        label = "Order No: 1234567890123456"
    draw.text((70, 85), "Sample order (fictional)", fill="black", font=font)
    draw.text((70, 210), label, fill="black", font=font)
    draw.text((70, 340), "Total: 28.50", fill="black", font=font)
    image.save(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
