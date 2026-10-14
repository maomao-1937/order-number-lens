"""Batch command-line interface."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from order_number_lens.core import collect_images, flag_batch_duplicates, inspect_image


def main() -> int:
    parser = argparse.ArgumentParser(description="Locally OCR order-number candidates from images; review all results")
    parser.add_argument("images", nargs="+", type=Path, help="Image files or a directory (non-recursive)")
    parser.add_argument("--expected-length", type=int, help="Require this exact number of digits")
    parser.add_argument("--csv-out", type=Path, help="Write local CSV review queue")
    parser.add_argument("--json-out", type=Path, help="Write detailed local JSON review queue")
    args = parser.parse_args()
    try:
        paths = collect_images(args.images)
        if args.expected_length is not None and not 1 <= args.expected_length <= 25:
            raise ValueError("--expected-length must be between 1 and 25")
        from rapidocr import RapidOCR

        engine = RapidOCR()
        rows = []
        for path in paths:
            try:
                rows.append(inspect_image(path, engine, args.expected_length))
            except (OSError, ValueError) as exc:
                rows.append({"file": str(path), "status": "review_needed", "candidate": None,
                             "reason": f"image could not be processed: {exc}",
                             "first_candidates": [], "enhanced_candidates": [], "ocr_context": []})
        flag_batch_duplicates(rows)
        if args.csv_out:
            with args.csv_out.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["file", "status", "candidate", "reason", "first_candidates", "enhanced_candidates"])
                writer.writeheader()
                for row in rows:
                    writer.writerow({key: json.dumps(row[key], ensure_ascii=False) if key.endswith("candidates") else row.get(key)
                                     for key in writer.fieldnames})
        if args.json_out:
            args.json_out.write_text(json.dumps({"warning": "Candidates are unverified OCR output. Review original images before use.",
                                                 "images": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for row in rows:
            print(f"{row['status']}\t{row.get('candidate') or '-'}\t{row['file']}\t{row['reason']}")
        print("All candidates require human comparison with the original image.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"order-number-lens: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
