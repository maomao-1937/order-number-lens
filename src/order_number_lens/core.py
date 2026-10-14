"""Image OCR and conservative extraction of long numeric order IDs."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


LABEL_RE = re.compile(r"(?:订单\s*(?:编号|号码|号)|order\s*(?:no\.?|number|#))", re.IGNORECASE)
DIGIT_GROUP_RE = re.compile(r"(?<!\d)\d(?:[\s\-]?\d){7,}(?!\d)")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class OCREngine(Protocol):
    def __call__(self, image: Any) -> Any: ...


@dataclass(frozen=True)
class OCRLine:
    text: str
    score: float


@dataclass(frozen=True)
class PassResult:
    candidates: tuple[str, ...]
    context: tuple[str, ...]
    best_score: float | None


def extract_lines(result: Any) -> list[OCRLine]:
    texts = getattr(result, "txts", None) or []
    scores = getattr(result, "scores", None) or []
    return [OCRLine(unicodedata.normalize("NFKC", str(text)).strip(), float(score))
            for text, score in zip(texts, scores) if str(text).strip()]


def extract_candidates(lines: list[OCRLine], min_digits: int = 8,
                       max_digits: int = 25) -> PassResult:
    if not (1 <= min_digits <= max_digits <= 25):
        raise ValueError("Digit limits must satisfy 1 <= min <= max <= 25")
    lines = [OCRLine(unicodedata.normalize("NFKC", line.text), line.score) for line in lines]
    found: dict[str, float] = {}
    context: list[str] = []
    for index, line in enumerate(lines):
        if not LABEL_RE.search(line.text):
            continue
        context.append(line.text)
        tail = LABEL_RE.split(line.text, maxsplit=1)[-1]
        nearby = [(tail, line.score)]
        if index + 1 < len(lines):
            nearby.append((lines[index + 1].text, lines[index + 1].score))
        for text, score in nearby:
            for match in DIGIT_GROUP_RE.finditer(text):
                digits = re.sub(r"\D", "", match.group())
                if min_digits <= len(digits) <= max_digits:
                    found[digits] = max(found.get(digits, 0.0), min(line.score, score))
                    context.append(text)
    return PassResult(tuple(found), tuple(dict.fromkeys(context)), max(found.values(), default=None))


def enhanced_image(path: Path) -> np.ndarray:
    with Image.open(path) as source:
        image = source.convert("RGB")
    if max(image.size) < 1600:
        image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    enhanced = ImageEnhance.Contrast(image.convert("L")).enhance(1.8).filter(
        ImageFilter.UnsharpMask(radius=1.5, percent=130))
    return np.asarray(enhanced)


def evaluate_passes(first: PassResult, second: PassResult,
                    expected_length: int | None = None) -> dict[str, Any]:
    all_candidates = sorted(set(first.candidates) | set(second.candidates))
    if expected_length is not None:
        if not 1 <= expected_length <= 25:
            raise ValueError("Expected length must be between 1 and 25")
        valid = [candidate for candidate in all_candidates if len(candidate) == expected_length]
    else:
        valid = all_candidates
    one = first.candidates[0] if len(first.candidates) == 1 else None
    two = second.candidates[0] if len(second.candidates) == 1 else None
    if not all_candidates:
        status, candidate, reason = "not_found", None, "no labeled long-number candidate found"
    elif not valid:
        status, candidate, reason = "review_needed", None, "candidate length does not match expected length"
    elif len(all_candidates) > 1:
        status, candidate, reason = "review_needed", None, "OCR passes or nearby labels disagree"
    elif one == two == valid[0]:
        status, candidate, reason = "consistent_candidate", valid[0], "both preprocessing passes returned the same digits; still verify against image"
    else:
        status, candidate, reason = "review_needed", valid[0] if len(valid) == 1 else None, "only one OCR pass found this candidate"
    return {
        "status": status,
        "candidate": candidate,
        "reason": reason,
        "first_candidates": list(first.candidates),
        "enhanced_candidates": list(second.candidates),
        "first_score": first.best_score,
        "enhanced_score": second.best_score,
        "ocr_context": list(dict.fromkeys((*first.context, *second.context))),
    }


def inspect_image(path: Path, engine: OCREngine, expected_length: int | None = None) -> dict[str, Any]:
    first = extract_candidates(extract_lines(engine(str(path))))
    second = extract_candidates(extract_lines(engine(enhanced_image(path))))
    return {"file": str(path), **evaluate_passes(first, second, expected_length)}


def collect_images(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        if item.is_dir():
            paths.extend(sorted(p for p in item.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES))
        elif item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES:
            paths.append(item)
        else:
            raise ValueError(f"Not a supported image or image directory: {item}")
    unique = list(dict.fromkeys(path.resolve() for path in paths))
    if not unique:
        raise ValueError("No supported images found")
    return unique


def flag_batch_duplicates(rows: list[dict[str, Any]]) -> None:
    seen: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("candidate"):
            seen.setdefault(row["candidate"], []).append(row)
    for matches in seen.values():
        if len(matches) > 1:
            for row in matches:
                row["status"] = "review_needed"
                row["reason"] = "same order number appears in multiple input files; verify whether intentional"
